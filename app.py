import os, zipfile, textwrap, pandas as pd
from pathlib import Path
import shutil

base = Path("/mnt/data/financial-risk-lab-v2")
if base.exists():
    shutil.rmtree(base)
base.mkdir(parents=True, exist_ok=True)

# Recast for org around $10M revenue
risk_data = pd.DataFrame([
    ["R001","Enrollment decline","Strategic",0.18,850000,153000,"Admissions","Open"],
    ["R002","Grant revenue shortfall","Financial",0.22,600000,132000,"Advancement","Open"],
    ["R003","Major donor attrition","Financial",0.15,900000,135000,"Development","Open"],
    ["R004","Compliance reporting failure","Compliance",0.08,450000,36000,"Compliance","Mitigating"],
    ["R005","Cyber incident","Operational",0.10,700000,70000,"IT","Mitigating"],
    ["R006","Vendor disruption","Operational",0.14,300000,42000,"Procurement","Open"],
    ["R007","Facility closure","BCM",0.06,500000,30000,"Operations","Mitigating"],
    ["R008","Staffing shortage","Operational",0.16,280000,44800,"HR","Open"],
    ["R009","Aid processing delays","Compliance",0.09,220000,19800,"Student Finance","Open"],
    ["R010","Reputation event","Strategic",0.07,650000,45500,"Executive","Open"],
], columns=["risk_id","risk_name","risk_category","probability","financial_impact","expected_loss","owner","status"])
risk_data.to_csv(base/"synthetic_risk_register.csv", index=False)

financials = pd.DataFrame([
    [2022, 5_900_000, 1_950_000, 250_000, 8_100_000, 7_700_000, 4_100_000, 1_650_000, 1_450_000],
    [2023, 6_150_000, 2_050_000, 300_000, 8_500_000, 8_050_000, 4_550_000, 1_850_000, 1_600_000],
    [2024, 7_100_000, 2_500_000, 400_000, 10_000_000, 9_350_000, 5_200_000, 2_100_000, 1_900_000],
], columns=[
    "fiscal_year","contributions","program_revenue","investment_income",
    "total_revenue","total_expenses","net_assets","cash_and_short_term_investments","operating_reserve"
])
financials.to_csv(base/"synthetic_990_financials.csv", index=False)

app_py = textwrap.dedent("""
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Financial Risk Lab", layout="wide")

def fmt_money(x):
    x = float(x)
    sign = "-" if x < 0 else ""
    x = abs(x)
    if x >= 1_000_000:
        return f"{sign}$%0.2fM" % (x / 1_000_000)
    if x >= 1_000:
        return f"{sign}$%0.0fK" % (x / 1_000)
    return f"{sign}${x:,.0f}"

def fmt_pct(x):
    return f"{x:.1f}%"

@st.cache_data
def load_data():
    risks = pd.read_csv("synthetic_risk_register.csv")
    fin = pd.read_csv("synthetic_990_financials.csv")
    return risks, fin

risks, fin = load_data()
base_2024 = fin[fin["fiscal_year"] == 2024].iloc[0]

st.title("Financial Risk Lab")
st.caption("Synthetic ERM + 990-style finance dashboard for a mission-driven organization with roughly $10M in annual revenue.")

with st.sidebar:
    st.header("Scenario deviations")
    st.write("Adjust deviations from the 2024 baseline.")
    contribution_dev = st.slider("Contributions deviation", -25, 15, -8, 1, format="%d%%")
    program_dev = st.slider("Program revenue deviation", -20, 20, -5, 1, format="%d%%")
    investment_dev = st.slider("Investment income deviation", -30, 30, 0, 1, format="%d%%")
    expense_dev = st.slider("Expense deviation", -10, 20, 4, 1, format="%d%%")

scenario_contributions = base_2024["contributions"] * (1 + contribution_dev / 100)
scenario_program = base_2024["program_revenue"] * (1 + program_dev / 100)
scenario_investment = base_2024["investment_income"] * (1 + investment_dev / 100)
scenario_revenue = scenario_contributions + scenario_program + scenario_investment
scenario_expenses = base_2024["total_expenses"] * (1 + expense_dev / 100)
scenario_margin = scenario_revenue - scenario_expenses
baseline_margin = base_2024["total_revenue"] - base_2024["total_expenses"]
margin_delta = scenario_margin - baseline_margin
revenue_delta = scenario_revenue - base_2024["total_revenue"]
expense_delta = scenario_expenses - base_2024["total_expenses"]
months_cash = (base_2024["cash_and_short_term_investments"] / scenario_expenses) * 12
reserve_coverage = base_2024["operating_reserve"] / scenario_expenses * 12

top1, top2, top3, top4 = st.columns(4)
top1.metric("2024 Baseline Revenue", fmt_money(base_2024["total_revenue"]))
top2.metric("Scenario Revenue", fmt_money(scenario_revenue), delta=fmt_money(revenue_delta))
top3.metric("Scenario Margin", fmt_money(scenario_margin), delta=fmt_money(margin_delta))
top4.metric("Months Cash on Hand", f"{months_cash:.1f}", delta=f"{months_cash - (base_2024['cash_and_short_term_investments']/base_2024['total_expenses']*12):.1f}")

st.subheader("Scenario summary")
summary = pd.DataFrame({
    "metric": [
        "Contributions", "Program revenue", "Investment income", "Total revenue",
        "Total expenses", "Operating margin", "Expense ratio", "Reserve coverage (months)"
    ],
    "baseline": [
        base_2024["contributions"], base_2024["program_revenue"], base_2024["investment_income"],
        base_2024["total_revenue"], base_2024["total_expenses"], baseline_margin,
        base_2024["total_expenses"] / base_2024["total_revenue"], (base_2024["operating_reserve"] / base_2024["total_expenses"]) * 12
    ],
    "scenario": [
        scenario_contributions, scenario_program, scenario_investment,
        scenario_revenue, scenario_expenses, scenario_margin,
        scenario_expenses / scenario_revenue if scenario_revenue != 0 else 0, reserve_coverage
    ]
})
summary["deviation"] = summary["scenario"] - summary["baseline"]

display = summary.copy()
for col in ["baseline", "scenario", "deviation"]:
    display[col] = display.apply(
        lambda r: fmt_pct(r[col] * 100) if r["metric"] == "Expense ratio" else (
            f"{r[col]:.1f}" if "months" in r["metric"].lower() else fmt_money(r[col])
        ),
        axis=1
    )
st.dataframe(display, use_container_width=True, hide_index=True)

left, right = st.columns(2)
with left:
    st.subheader("Top risks by expected loss")
    risk_view = risks.sort_values("expected_loss", ascending=False)[["risk_name", "expected_loss"]].copy()
    risk_view = risk_view.set_index("risk_name")
    st.bar_chart(risk_view)

with right:
    st.subheader("Impact by risk category")
    cat_view = risks.groupby("risk_category", as_index=True)["financial_impact"].sum().sort_values(ascending=False)
    st.bar_chart(cat_view)

st.subheader("Risk register")
risk_display = risks.copy()
risk_display["probability"] = risk_display["probability"].map(lambda x: f"{x:.0%}")
risk_display["financial_impact"] = risk_display["financial_impact"].map(fmt_money)
risk_display["expected_loss"] = risk_display["expected_loss"].map(fmt_money)
st.dataframe(risk_display, use_container_width=True, hide_index=True)

st.subheader("Synthetic 990-style financials")
fin_display = fin.copy()
money_cols = [c for c in fin_display.columns if c != "fiscal_year"]
for c in money_cols:
    fin_display[c] = fin_display[c].map(fmt_money)
st.dataframe(fin_display, use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown("### What changed in this version")
st.markdown(\"\"\"
- Numbers are scaled closer to a real organization with about **$10M** in annual revenue
- Dollar formatting uses **$K / $M** instead of long strings of zeros
- Scenario controls now show **deviations from baseline**
- Summary table shows **baseline vs scenario vs deviation**
\"\"\")
""").strip()

(base/"app.py").write_text(app_py)

requirements = "streamlit>=1.35.0\npandas>=2.2.0\n"
(base/"requirements.txt").write_text(requirements)

readme = textwrap.dedent("""
# Financial Risk Lab v2

A refined starter repo for a finance-heavy ERM portfolio project using synthetic data sized to a mission-driven organization with about $10M in annual revenue.

## Included
- `app.py` — Streamlit dashboard
- `synthetic_risk_register.csv` — risk register with expected loss values
- `synthetic_990_financials.csv` — 990-style financial baseline
- `requirements.txt`
- `README.md`

## Improvements in v2
- Cleaner money formatting with `$K` and `$M`
- Scenario sliders calculate deviations from a realistic baseline
- Summary view compares baseline, scenario, and deviation side by side

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
