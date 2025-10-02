import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agent.tools import revenue_vs_budget, ebitda_proxy, gross_margin_trend, opex_breakdown, cash_runway


def test_rev_vs_budget():
    a,b = revenue_vs_budget("2025-06")
    assert a > 0 and b > 0 and abs(a-b) >= 0

def test_ebitda_proxy():
    val = ebitda_proxy("2025-06")
    assert isinstance(val, float)

def test_gm_trend():
    df = gross_margin_trend(last_n=3)
    assert len(df) <= 3
    assert "gm_pct" in df.columns

def test_opex_breakdown():
    df = opex_breakdown("2025-06")
    assert "account" in df.columns
    assert "amount_usd" in df.columns

def test_cash_runway():
    cash, runway = cash_runway()
    assert cash >= 0
    # runway can be None (no burn) or positive
    assert (runway is None) or (runway > 0)
