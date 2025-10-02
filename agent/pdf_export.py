import pandas as pd
import plotly.express as px
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from agent import tools

def export_pdf(output_file="fpa_export.pdf"):
    # Revenue vs Budget figure
    actuals = pd.read_csv("fixtures/actuals.csv")
    latest_month = sorted(actuals["month"].unique())[-1]
    a, b = tools.revenue_vs_budget(latest_month)
    fig1 = px.bar(
        pd.DataFrame({"Label": ["Actual", "Budget"], "USD": [a, b]}),
        x="Label", y="USD", title=f"Revenue vs Budget — {latest_month}"
    )

    # Cash trend figure
    cash_df = pd.read_csv("fixtures/cash.csv")

    if "cash_usd" in cash_df.columns:
        cash_df["amount_usd"] = cash_df["cash_usd"]
    elif "cash" in cash_df.columns:
        cash_df["amount_usd"] = cash_df["cash"]
    else:
        raise ValueError("cash.csv must contain either 'cash_usd' or 'cash' column")

    agg = cash_df.groupby("month", as_index=False)["amount_usd"].sum()
    fig2 = px.line(agg, x="month", y="amount_usd", markers=True, title="Cash Trend (USD)")

    # Save plots to temporary files
    tmp1 = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp2 = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    fig1.write_image(tmp1.name, scale=2)
    fig2.write_image(tmp2.name, scale=2)

    # Write to PDF
    c = canvas.Canvas(output_file, pagesize=A4)
    w, h = A4
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, h-50, "FP&A Snapshot")
    c.setFont("Helvetica", 10)
    c.drawString(50, h-65, "Auto-generated from current fixtures")
    c.drawImage(ImageReader(tmp1.name), 50, h-380, width=500, height=280, preserveAspectRatio=True, anchor='nw')

    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, h-50, "Cash Trend")
    c.drawImage(ImageReader(tmp2.name), 50, h-380, width=500, height=280, preserveAspectRatio=True, anchor='nw')

    c.save()
    return output_file
