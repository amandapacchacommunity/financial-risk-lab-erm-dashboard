import pandas as pd
import streamlit as st

st.set_page_config(page_title="Financial Risk Lab", layout="wide")

def fmt_money(x):
    x = float(x)
    sign = "-" if x < 0 else ""
    x = abs(x)
    if x >= 1000000:
        return f"{sign}${x/1000000:.2f}M"
    if x >= 1000:
        return f"{sign}${x/1000:.0f}K"
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
    st.divider()
    preset = st.selectbox("Preset scenario", ["Custom", "Base Case", "Soft Revenue Dip", "Expense Pressure", "Stress Case"])

if preset == "Base Case":
    contribution_dev, program_dev, investment_dev, expense_dev = 0, 0, 0, 0
elif preset == "Soft Revenue Dip":
    contribution_dev, program_dev, investment_dev, expense_dev = -6, -4, 0, 3
elif preset == "Expense Pressure":
    contribution_dev, program_dev, investment_dev, expense_dev = -3, 0, 0, 7
elif preset == "Stress Case":
    contribution_dev, program_dev, investment_dev, expense_dev = -12, -8, -10, 10

scenario_contributions = base_2024["contributions"] * (1 + contribution_dev / 100)
scenario_program = base_2024["program_revenue"] * (1 + program_dev / 100)
scenario_investment = base_2024["investment_income"] * (1 + investment_dev / 100)
scenario_revenue = scenario_contributions + scenario_program + scenario_investment
scenario_expenses = base_2024["total_expenses"] * (1 + expense_dev / 100)
scenario_margin = scenario_revenue - scenario_expenses
baseline_margin = base_2024["total_revenue"] - base_2024["total_expenses"]
revenue_delta = scenario_revenue - base_2024["total_revenue"]
expense_delta = scenario_expenses - base_2024["total_expenses"]
margin_delta = scenario_margin - baseline_margin
baseline_months_cash = (base_2024["cash_and_short_term_investments"] / base_2024["total_expenses"]) * 12
months_cash = (base_2024["cash_and_short_term_investments"] / scenario_expenses) * 12
reserve_coverage = (base_2024["operating_reserve"] / scenario_expenses) * 12

r1, r2, r3, r4 = st.columns(4)
r1.metric("2024 Baseline Revenue", fmt_money(base_2024["total_revenue"]))
r2.metric("Scenario Revenue", fmt_money(scenario_revenue), delta=fmt_money(revenue_delta))
r3.metric("Scenario Expenses", fmt_money(scenario_expenses), delta=fmt_money(expense_delta))
r4.metric("Scenario Margin", fmt_money(scenario_margin), delta=fmt_money(margin_delta))

r5, r6, r7, r8 = st.columns(4)
r5.metric("Months Cash on Hand", f"{months_cash:.1f}", delta=f"{months_cash - baseline_months_cash:.1f}")
r6.metric("Reserve Coverage", f"{reserve_coverage:.1f} mo")
r7.metric("Expense Ratio", fmt_pct((scenario_expenses / scenario_revenue) * 100 if scenario_revenue else 0))
r8.metric("Total Expected Loss", fmt_money(risks["expected_loss"].sum()))

summary = pd.DataFrame({
    "metric": [
        "Contributions", "Program revenue", "Investment income", "Total revenue",
        "Total expenses", "Operating margin", "Expense ratio", "Reserve coverage (months)"
    ],
    "baseline": [
        base_2024["contributions"], base_2024["program_revenue"], base_2024["investment_income"],
        base_2024["total_revenue"], base_2024["total_expenses"], baseline_margin,
        (base_2024["total_expenses"] / base_2024["total_revenue"]) * 100,
        (base_2024["operating_reserve"] / base_2024["total_expenses"]) * 12
    ],
    "scenario": [
        scenario_contributions, scenario_program, scenario_investment,
        scenario_revenue, scenario_expenses, scenario_margin,
        (scenario_expenses / scenario_revenue) * 100 if scenario_revenue else 0,
        reserve_coverage
    ]
})
summary["deviation"] = summary["scenario"] - summary["baseline"]

def format_row(metric, value):
    if metric == "Expense ratio":
        return fmt_pct(value)
    if "months" in metric.lower():
        return f"{value:.1f}"
    return fmt_money(value)

display = summary.copy()
for col in ["baseline", "scenario", "deviation"]:
    display[col] = [format_row(m, v) for m, v in zip(display["metric"], display[col])]

st.subheader("Scenario summary")
st.dataframe(display, use_container_width=True, hide_index=True)

left, right = st.columns(2)

with left:
    st.subheader("Top risks by expected loss")
    risk_view = risks.sort_values("expected_loss", ascending=False)[["risk_name", "expected_loss"]].set_index("risk_name")
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
for c in fin_display.columns:
    if c != "fiscal_year":
        fin_display[c] = fin_display[c].map(fmt_money)
st.dataframe(fin_display, use_container_width=True, hide_index=True)