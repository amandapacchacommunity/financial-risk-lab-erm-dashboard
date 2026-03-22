# Financial Risk Lab Starter

A small starter repo for a finance-heavy ERM portfolio project using synthetic data.

## What is included
- `app.py` — Streamlit dashboard
- `synthetic_risk_register.csv` — sample risk register with expected loss
- `synthetic_990_financials.csv` — sample 990-style nonprofit financials
- `requirements.txt` — basic dependencies

## What this demonstrates
- Expected loss modeling
- Risk ranking by financial exposure
- Scenario modeling for contributions, program revenue, and expenses
- Reserve and liquidity-oriented thinking for nonprofit finance

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Suggested repo framing
You can describe this as:
- a synthetic nonprofit financial risk dashboard
- an ERM scenario modeling lab
- a portfolio sample showing how operational and compliance risks can be translated into financial exposure

## Easy ways to customize
- Replace the synthetic organization with a museum, higher-ed institution, or mission-driven nonprofit
- Add IRS Form 990 inspired fields such as liabilities, functional expenses, and donor concentration
- Add business continuity impact metrics such as downtime cost and recovery targets