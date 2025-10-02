# FP&A Agent (Mini CFO Copilot)

A small, end-to-end Streamlit app that answers simple finance questions from CSVs:
- Revenue vs Budget (USD)
- Gross Margin % trend
- Opex breakdown
- Cash runway

## Quick start

```bash
# 1) Create and activate a virtualenv (recommended)
python3 -m venv .venv && source .venv/bin/activate

# 2) Install deps
pip install -r requirements.txt

# 3) Run tests (uses sample fixtures)
pytest -q

# 4) Launch the app
streamlit run app.py
```

Open the app in your browser (the URL will appear in the terminal).

## Data

Place CSVs under `fixtures/` with these schemas (sample files included):

- **actuals.csv** / **budget.csv**
    - `entity,account,currency,month,amount`
    - `month` format: `YYYY-MM` (e.g., `2025-06`)
    - `account` examples: `Revenue`, `COGS`, `Opex:Sales`, `Opex:R&D`, `Opex:G&A`

- **fx.csv**
    - `month,currency,rate_to_usd`

- **cash.csv**
    - `month,currency,cash`

You can replace the sample CSVs with your own. If you have an .xlsx link, export sheets to CSV and drop them into `fixtures/`.

## App Structure

```
app.py                 # Streamlit UI + response rendering
agent/
  intent.py            # naive intent/argument parser
  tools.py             # CSV loaders and metric functions
tests/
  test_metrics.py      # basic coverage for metrics
fixtures/              # sample data for quick run
```

## Example questions

- "What was June 2025 revenue vs budget in USD?"
- "Show Gross Margin % trend for the last 3 months."
- "Break down Opex by category for June 2025."
- "What is our cash runway right now?"

## Optional: Export PDF

Click **Export PDF** to generate a 1–2 page PDF with a Revenue vs Budget chart and Cash trend, using current fixtures.
