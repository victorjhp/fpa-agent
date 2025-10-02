import streamlit as st
import pandas as pd
import plotly.express as px
from agent.intent import detect_intent
from agent import tools
from agent.pdf_export import export_pdf  
import kaleido


st.set_page_config(page_title="FP&A Agent", layout="wide")
st.title("💼 FP&A Agent — Mini CFO Copilot")

st.markdown("""Ask about revenue vs budget, gross margin %, opex breakdown, or cash runway.
Examples:
- What was **June 2025** revenue vs budget in USD?
- Show **Gross Margin %** trend for the **last 3 months**.
- Break down **Opex** by category for **June 2025**.
- What is our **cash runway** right now?
""")

q = st.text_input("Ask a question")
col1, col2 = st.columns([3,2])
chart_placeholder = st.empty()
df_cache = {}

def show_rev_vs_budget(month: str, currency: str):
    a, b = tools.revenue_vs_budget(month, currency=currency)
    st.subheader(f"Revenue vs Budget — {month} ({currency})")
    st.metric("Actual (USD)", f"{a:,.0f}")
    st.metric("Budget (USD)", f"{b:,.0f}")
    fig = px.bar(pd.DataFrame({
        "Label": ["Actual", "Budget"],
        "USD": [a, b]
    }), x="Label", y="USD", title=f"Revenue vs Budget — {month}")
    chart_placeholder.plotly_chart(fig, use_container_width=True)

def show_gm_trend(last_n: int):
    df = tools.gross_margin_trend(last_n=last_n)
    st.subheader(f"Gross Margin % — Last {last_n} months")
    if df.empty:
        st.info("No data.")
        return
    fig = px.line(df, x="month", y="gm_pct", markers=True, title="Gross Margin % Trend")
    chart_placeholder.plotly_chart(fig, use_container_width=True)
    st.dataframe(df)

def show_opex_breakdown(month: str):
    df = tools.opex_breakdown(month)
    st.subheader(f"Opex Breakdown — {month}")
    if df.empty:
        st.info("No data.")
        return
    fig = px.pie(df, names="account", values="amount_usd", title="Opex by Category")
    chart_placeholder.plotly_chart(fig, use_container_width=True)
    st.dataframe(df)


def ebitda(month: str, currency: str = "USD"):
    actuals = pd.read_csv("fixtures/actuals.csv")
    budget = pd.read_csv("fixtures/budget.csv")
    fx = pd.read_csv("fixtures/fx.csv")

    act = actuals[actuals["month"] == month]
    bud = budget[budget["month"] == month]

    revenue = act[act["account"] == "Revenue"]["amount"].sum()
    cogs = act[act["account"] == "COGS"]["amount"].sum()
    opex = act[act["account"].str.startswith("Opex")]["amount"].sum()

    ebitda_val = revenue - cogs - opex
    return ebitda_val



def show_cash_runway():
    cash, runway = tools.cash_runway()
    st.subheader("Cash Runway")
    st.metric("Cash (USD)", f"{cash:,.0f}")
    if runway is None:
        st.write("Runway: N/A (no burn or negative burn).")
    else:
        st.metric("Runway (months)", f"{runway:,.1f}")

    cash_df = pd.read_csv("fixtures/cash.csv")

    if "cash_usd" in cash_df.columns:
        cash_df["amount_usd"] = cash_df["cash_usd"]
    elif "cash" in cash_df.columns:
        cash_df["amount_usd"] = cash_df["cash"]
    else:
        raise ValueError("cash.csv must contain 'cash_usd' or 'cash' column")

    agg = cash_df.groupby("month", as_index=False)["amount_usd"].sum()
    fig = px.line(agg, x="month", y="amount_usd", markers=True, title="Cash Trend (USD)")
    chart_placeholder.plotly_chart(fig, use_container_width=True)


if q:
    parsed = detect_intent(q)
    with st.expander("Parsed Query", expanded=False):
        st.json(parsed.__dict__)

    if parsed.intent == "rev_vs_budget":
        if parsed.month:
            show_rev_vs_budget(parsed.month, parsed.currency)
        else:
            st.info("Please include a month like 'June 2025'.")

    elif parsed.intent == "gm_trend":
        show_gm_trend(parsed.last_n or 3)

    elif parsed.intent == "opex_breakdown":
        if parsed.month:
            show_opex_breakdown(parsed.month)
        else:
            st.info("Please include a month like 'June 2025'.")

    elif parsed.intent == "cash_runway":
        show_cash_runway()
    else:
        st.info("I can help with: revenue vs budget, GM% trend, Opex breakdown, and cash runway.")

st.divider()
st.subheader("Optional: Export PDF")

if st.button("Generate PDF Report"):
    try:
        pdf_path = export_pdf()   
        with open(pdf_path, "rb") as f:
            st.download_button("Download PDF", data=f, file_name=pdf_path, mime="application/pdf")
    except Exception as e:
        st.warning(f"PDF export failed: {e}")
