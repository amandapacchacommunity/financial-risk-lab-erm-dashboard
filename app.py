import pandas as pd
import streamlit as st

st.set_page_config(page_title="Financial Risk Lab", layout="wide")

@st.cache_data
def load_data():
    risks = pd.read_csv("synthetic_risk_register.csv")
    fin = pd.read_csv("synthetic_990_financials.csv")
    return risks, fin

risks, fin = load_data()

st.title("Financial Risk Lab")
st.caption("Synthetic ERM + 990-style finance dashboard for portfolio use.")

with st.sidebar:
    st.header("Scenario Controls")
    donation_drop = st.slider("Contribution decline %", 0, 40, 10, 5)
    program_drop = st.slider("Program revenue decline %", 0, 30, 5, 5)
    expense_increase = st.slider("Expense increase %", 0, 25, 5, 5)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Expected Loss", f"${risks['expected_loss'].sum():,.0f}")
col2.metric("Top Financial Impact", f"${risks['financial_impact'].max():,.0f}")
col3.metric("2024 Operating Reserve", f"${fin.loc[fin['fiscal_year']==2024, 'operating_reserve'].iloc[0]:,.0f}")
col4.metric("2024 Net Assets", f"${fin.loc[fin['fiscal_year']==2024, 'net_assets'].iloc[0]:,.0f}")

st.subheader("Risk Register")
st.dataframe(risks, use_container_width=True)

left, right = st.columns(2)

with left:
    st.subheader("Expected Loss by Risk")
    loss_view = risks.sort_values("expected_loss", ascending=False).set_index("risk_name")[["expected_loss"]]
    st.bar_chart(loss_view)

with right:
    st.subheader("Financial Impact by Category")
    cat_view = risks.groupby("risk_category", as_index=True)["financial_impact"].sum().sort_values(ascending=False)
    st.bar_chart(cat_view)

st.subheader("Synthetic 990-Style Financials")
st.dataframe(fin, use_container_width=True)

base_2024 = fin[fin["fiscal_year"] == 2024].iloc[0]
scenario_revenue = (
    base_2024["contributions"] * (1 - donation_drop / 100)
    + base_2024["program_revenue"] * (1 - program_drop / 100)
    + base_2024["investment_income"]
)
scenario_expenses = base_2024["total_expenses"] * (1 + expense_increase / 100)
scenario_margin = scenario_revenue - scenario_expenses
months_cash = (base_2024["cash_and_short_term_investments"] / scenario_expenses) * 12

st.subheader("Scenario Model")
s1, s2, s3, s4 = st.columns(4)
s1.metric("Scenario Revenue", f"${scenario_revenue:,.0f}")
s2.metric("Scenario Expenses", f"${scenario_expenses:,.0f}")
s3.metric("Scenario Margin", f"${scenario_margin:,.0f}")
s4.metric("Months Cash on Hand", f"{months_cash:.1f}")

scenario_df = pd.DataFrame({
    "metric": ["Contributions", "Program Revenue", "Investment Income", "Total Revenue", "Total Expenses", "Scenario Margin"],
    "value": [
        base_2024["contributions"] * (1 - donation_drop / 100),
        base_2024["program_revenue"] * (1 - program_drop / 100),
        base_2024["investment_income"],
        scenario_revenue,
        scenario_expenses,
        scenario_margin
    ]
})
st.dataframe(scenario_df, use_container_width=True)

st.markdown("---")
st.markdown("### Suggested next enhancements")
st.markdown("""
- Add donor concentration risk
- Add liquidity and reserve ratios
- Add business impact analysis with recovery time objectives
- Add Monte Carlo simulation for portfolio-wide loss ranges
""")