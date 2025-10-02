from __future__ import annotations
import pandas as pd
from typing import Tuple, Optional
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "fixtures"

def _load_csv(name: str) -> pd.DataFrame:
    p = DATA_DIR / name
    if not p.exists():
        raise FileNotFoundError(f"Missing fixtures/{name}. Place CSVs under fixtures/.")
    return pd.read_csv(p)

def load_data():
    actuals = _load_csv("actuals.csv")
    budget  = _load_csv("budget.csv")
    fx      = _load_csv("fx.csv")
    cash    = _load_csv("cash.csv")


    for df in (actuals, budget):
        if "account_category" in df.columns and "account" not in df.columns:
            df.rename(columns={"account_category": "account"}, inplace=True)

    if "cash_usd" in cash.columns and "cash" not in cash.columns:
        cash.rename(columns={"cash_usd": "cash"}, inplace=True)

    if "currency" not in cash.columns:
        cash["currency"] = "USD"


    for df in (actuals, budget, fx, cash):
        if "month" in df.columns:
            df["month"] = df["month"].astype(str)

    return actuals, budget, fx, cash


def to_usd(df: pd.DataFrame, fx: pd.DataFrame, amount_col: str = "amount") -> pd.DataFrame:
    merged = df.merge(fx, on=["month","currency"], how="left")
    merged["rate_to_usd"] = merged["rate_to_usd"].fillna(1.0)
    merged["amount_usd"] = merged[amount_col] * merged["rate_to_usd"]
    return merged

def revenue_vs_budget(month: str, currency: str="USD") -> Tuple[float,float]:
    actuals, budget, fx, _ = load_data()
    a = actuals[(actuals["account"]=="Revenue") & (actuals["month"]==month)]
    b = budget[(budget["account"]=="Revenue") & (budget["month"]==month)]
    a_usd = to_usd(a, fx)["amount_usd"].sum()
    b_usd = to_usd(b, fx)["amount_usd"].sum()
    return a_usd, b_usd

def gross_margin_trend(last_n: int=3) -> pd.DataFrame:
    actuals, _, fx, _ = load_data()
    # aggregate by month for Revenue & COGS
    rev = actuals[actuals["account"]=="Revenue"].groupby(["month","currency"], as_index=False)["amount"].sum()
    cogs= actuals[actuals["account"]=="COGS"].groupby(["month","currency"], as_index=False)["amount"].sum()
    rev_usd = to_usd(rev, fx).groupby("month", as_index=False)["amount_usd"].sum().rename(columns={"amount_usd":"revenue_usd"})
    cogs_usd= to_usd(cogs,fx).groupby("month", as_index=False)["amount_usd"].sum().rename(columns={"amount_usd":"cogs_usd"})
    df = rev_usd.merge(cogs_usd, on="month", how="outer").fillna(0.0)
    df["gm_pct"] = (df["revenue_usd"] - df["cogs_usd"]) / df["revenue_usd"].replace(0, pd.NA) * 100
    df = df.sort_values("month").tail(last_n)
    return df

def opex_breakdown(month: str) -> pd.DataFrame:
    actuals, _, fx, _ = load_data()
    opex = actuals[(actuals["account"].str.startswith("Opex:")) & (actuals["month"]==month)]
    if opex.empty:
        return pd.DataFrame(columns=["account","amount_usd"])
    opex_usd = to_usd(opex, fx).groupby("account", as_index=False)["amount_usd"].sum()
    return opex_usd.sort_values("amount_usd", ascending=False)

def cash_runway() -> Tuple[float, Optional[float]]:
    actuals, _, fx, cash = load_data()
    # net burn = (COGS + Opex total) - Revenue (positive number means burning cash)
    # compute last 3 months average
    rev = actuals[actuals["account"]=="Revenue"].groupby(["month","currency"], as_index=False)["amount"].sum()
    cogs= actuals[actuals["account"]=="COGS"].groupby(["month","currency"], as_index=False)["amount"].sum()
    opex= actuals[actuals["account"].str.startswith("Opex:")].groupby(["month","currency"], as_index=False)["amount"].sum()

    rev_usd  = to_usd(rev, fx).groupby("month", as_index=False)["amount_usd"].sum().rename(columns={"amount_usd":"rev"})
    cogs_usd = to_usd(cogs,fx).groupby("month", as_index=False)["amount_usd"].sum().rename(columns={"amount_usd":"cogs"})
    opex_usd = to_usd(opex,fx).groupby("month", as_index=False)["amount_usd"].sum().rename(columns={"amount_usd":"opex"})

    burn = rev_usd.merge(cogs_usd, on="month", how="outer").merge(opex_usd, on="month", how="outer").fillna(0.0)
    burn["net_burn"] = (burn["cogs"] + burn["opex"]) - burn["rev"]
    burn = burn.sort_values("month").tail(3)
    avg_burn = burn["net_burn"].mean()
    # cash (assume last row is current)
    cash_usd = to_usd(cash.rename(columns={"cash":"amount"}), fx, amount_col="amount").rename(columns={"amount_usd":"cash_usd"})
    if cash_usd.empty:
        return 0.0, None
    latest_cash = cash_usd.sort_values("month")["cash_usd"].iloc[-1]
    runway_months = (latest_cash / avg_burn) if avg_burn > 0 else None
    return float(latest_cash), (float(runway_months) if runway_months is not None else None)

def ebitda_proxy(month: str) -> float:
    actuals, _, fx, _ = load_data()
    rev  = actuals[(actuals["account"]=="Revenue") & (actuals["month"]==month)]
    cogs = actuals[(actuals["account"]=="COGS") & (actuals["month"]==month)]
    opex = actuals[(actuals["account"].str.startswith("Opex:")) & (actuals["month"]==month)]
    rev_usd  = to_usd(rev, fx)["amount_usd"].sum()
    cogs_usd = to_usd(cogs,fx)["amount_usd"].sum()
    opex_usd = to_usd(opex,fx)["amount_usd"].sum()
    return float(rev_usd - cogs_usd - opex_usd)
