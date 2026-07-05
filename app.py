"""
Customer Engagement & Product Utilization Analytics for Retention Strategy
European Central Bank — Streamlit Dashboard
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --------------------------------------------------------------------------
# Page config
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Retention Analytics | European Central Bank",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------
# Styling
# --------------------------------------------------------------------------
st.markdown("""
<style>
    .kpi-card {
        background-color: #f8f9fb;
        border: 1px solid #e3e6eb;
        border-radius: 10px;
        padding: 18px 16px;
        text-align: center;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 700;
        color: #0b2545;
        margin: 0;
    }
    .kpi-label {
        font-size: 13px;
        color: #5b6673;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }
    .kpi-sub {
        font-size: 12px;
        color: #8a94a3;
        margin-top: 4px;
    }
    section[data-testid="stSidebar"] {
        background-color: #0b2545;
    }
    section[data-testid="stSidebar"] * {
        color: #f0f2f5 !important;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("European_Bank.csv")

    # Engagement profile classification
    balance_median = df["Balance"].median()

    def classify(row):
        active = row["IsActiveMember"] == 1
        multi_product = row["NumOfProducts"] >= 2
        high_balance = row["Balance"] > balance_median
        if active and multi_product:
            return "Active & Engaged"
        elif active and not multi_product:
            return "Active, Low-Product"
        elif not active and high_balance:
            return "Inactive, High-Balance"
        else:
            return "Inactive & Disengaged"

    df["EngagementProfile"] = df.apply(classify, axis=1)

    # Relationship Strength Index (0-100): blend of activity, product depth,
    # credit card ownership and tenure
    df["RelationshipStrengthIndex"] = (
        (df["IsActiveMember"] * 35)
        + (df["NumOfProducts"].clip(upper=4) / 4 * 35)
        + (df["HasCrCard"] * 15)
        + (df["Tenure"].clip(upper=10) / 10 * 15)
    ).round(1)

    # At-risk premium customer flag: high balance/salary but disengaged
    salary_75 = df["EstimatedSalary"].quantile(0.75)
    balance_75 = df["Balance"].quantile(0.75)
    df["AtRiskPremium"] = (
        (df["IsActiveMember"] == 0)
        & ((df["Balance"] >= balance_75) | (df["EstimatedSalary"] >= salary_75))
    )

    return df

df_raw = load_data()

# --------------------------------------------------------------------------
# Sidebar filters
# --------------------------------------------------------------------------
st.sidebar.title("🏦 Retention Analytics")
st.sidebar.caption("European Central Bank — Customer Engagement Study")
st.sidebar.markdown("---")
st.sidebar.subheader("Filters")

geo_options = sorted(df_raw["Geography"].unique().tolist())
geo_sel = st.sidebar.multiselect("Geography", geo_options, default=geo_options)

gender_options = sorted(df_raw["Gender"].unique().tolist())
gender_sel = st.sidebar.multiselect("Gender", gender_options, default=gender_options)

engagement_options = sorted(df_raw["EngagementProfile"].unique().tolist())
engagement_sel = st.sidebar.multiselect(
    "Engagement Profile", engagement_options, default=engagement_options
)

product_min, product_max = int(df_raw["NumOfProducts"].min()), int(df_raw["NumOfProducts"].max())
product_range = st.sidebar.slider(
    "Number of Products", product_min, product_max, (product_min, product_max)
)

balance_min, balance_max = float(df_raw["Balance"].min()), float(df_raw["Balance"].max())
balance_range = st.sidebar.slider(
    "Balance Range (€)", balance_min, balance_max, (balance_min, balance_max),
    format="€%.0f"
)

salary_min, salary_max = float(df_raw["EstimatedSalary"].min()), float(df_raw["EstimatedSalary"].max())
salary_range = st.sidebar.slider(
    "Estimated Salary Range (€)", salary_min, salary_max, (salary_min, salary_max),
    format="€%.0f"
)

age_min, age_max = int(df_raw["Age"].min()), int(df_raw["Age"].max())
age_range = st.sidebar.slider("Age Range", age_min, age_max, (age_min, age_max))

st.sidebar.markdown("---")
st.sidebar.caption("Data: European_Bank.csv · 10,000 customers · FY2025")

# Apply filters
df = df_raw[
    (df_raw["Geography"].isin(geo_sel))
    & (df_raw["Gender"].isin(gender_sel))
    & (df_raw["EngagementProfile"].isin(engagement_sel))
    & (df_raw["NumOfProducts"].between(*product_range))
    & (df_raw["Balance"].between(*balance_range))
    & (df_raw["EstimatedSalary"].between(*salary_range))
    & (df_raw["Age"].between(*age_range))
]

if df.empty:
    st.warning("No customers match the current filter selection. Please broaden your filters.")
    st.stop()

# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------
st.title("Customer Engagement & Product Utilization Analytics")
st.caption("Retention Strategy Dashboard · Behavioral & Relationship-Strength View of Churn")

# --------------------------------------------------------------------------
# KPI calculations
# --------------------------------------------------------------------------
overall_churn = df["Exited"].mean() * 100

active_churn = df.loc[df["IsActiveMember"] == 1, "Exited"].mean() * 100 if (df["IsActiveMember"] == 1).any() else 0
inactive_churn = df.loc[df["IsActiveMember"] == 0, "Exited"].mean() * 100 if (df["IsActiveMember"] == 0).any() else 0
engagement_retention_ratio = (inactive_churn / active_churn) if active_churn > 0 else np.nan

single_prod_churn = df.loc[df["NumOfProducts"] == 1, "Exited"].mean() * 100 if (df["NumOfProducts"] == 1).any() else 0
multi_prod_churn = df.loc[df["NumOfProducts"] >= 2, "Exited"].mean() * 100 if (df["NumOfProducts"] >= 2).any() else 0
product_depth_index = (single_prod_churn - multi_prod_churn)

balance_median = df["Balance"].median()
high_bal = df[df["Balance"] > balance_median]
high_balance_disengagement_rate = (
    (high_bal["IsActiveMember"] == 0).mean() * 100 if len(high_bal) > 0 else 0
)

cc_churn = df.loc[df["HasCrCard"] == 1, "Exited"].mean() * 100 if (df["HasCrCard"] == 1).any() else 0
no_cc_churn = df.loc[df["HasCrCard"] == 0, "Exited"].mean() * 100 if (df["HasCrCard"] == 0).any() else 0
credit_card_stickiness = (no_cc_churn - cc_churn)

relationship_strength_index = df["RelationshipStrengthIndex"].mean()

# --------------------------------------------------------------------------
# KPI Row
# --------------------------------------------------------------------------
k1, k2, k3, k4, k5, k6 = st.columns(6)

with k1:
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-label">Overall Churn Rate</p>
        <p class="kpi-value">{overall_churn:.1f}%</p>
        <p class="kpi-sub">{df["Exited"].sum():,} of {len(df):,} customers</p>
    </div>""", unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-label">Engagement Retention Ratio</p>
        <p class="kpi-value">{engagement_retention_ratio:.2f}x</p>
        <p class="kpi-sub">Inactive vs active churn rate</p>
    </div>""", unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-label">Product Depth Index</p>
        <p class="kpi-value">{product_depth_index:+.1f} pp</p>
        <p class="kpi-sub">Single vs multi-product churn gap</p>
    </div>""", unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-label">High-Balance Disengagement</p>
        <p class="kpi-value">{high_balance_disengagement_rate:.1f}%</p>
        <p class="kpi-sub">Above-median balance, inactive</p>
    </div>""", unsafe_allow_html=True)

with k5:
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-label">Credit Card Stickiness</p>
        <p class="kpi-value">{credit_card_stickiness:+.1f} pp</p>
        <p class="kpi-sub">No-card vs card churn gap</p>
    </div>""", unsafe_allow_html=True)

with k6:
    st.markdown(f"""
    <div class="kpi-card">
        <p class="kpi-label">Relationship Strength Index</p>
        <p class="kpi-value">{relationship_strength_index:.1f}/100</p>
        <p class="kpi-sub">Avg. across filtered customers</p>
    </div>""", unsafe_allow_html=True)

st.markdown("")

# --------------------------------------------------------------------------
# Tabs — Core Modules
# --------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Engagement vs Churn",
    "🧩 Product Utilization",
    "🎯 High-Value Disengaged Detector",
    "💪 Retention Strength Scoring",
])

# ==========================================================================
# TAB 1 — Engagement vs Churn Overview
# ==========================================================================
with tab1:
    st.subheader("Engagement vs Churn Overview")

    c1, c2 = st.columns([1, 1])

    with c1:
        profile_churn = (
            df.groupby("EngagementProfile")["Exited"]
            .agg(["mean", "count"])
            .reset_index()
        )
        profile_churn["mean"] = profile_churn["mean"] * 100
        profile_churn = profile_churn.sort_values("mean", ascending=False)

        fig = px.bar(
            profile_churn, x="EngagementProfile", y="mean",
            text=profile_churn["mean"].round(1).astype(str) + "%",
            color="EngagementProfile",
            labels={"mean": "Churn Rate (%)", "EngagementProfile": "Engagement Profile"},
            title="Churn Rate by Engagement Profile",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False, yaxis_title="Churn Rate (%)")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        active_counts = df["IsActiveMember"].map({1: "Active", 0: "Inactive"}).value_counts().reset_index()
        active_counts.columns = ["Status", "Count"]
        fig2 = px.pie(
            active_counts, names="Status", values="Count",
            title="Active vs Inactive Members (Filtered)",
            color="Status",
            color_discrete_map={"Active": "#2e7d32", "Inactive": "#c62828"},
            hole=0.5,
        )
        st.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns([1, 1])
    with c3:
        active_churn_df = pd.DataFrame({
            "Status": ["Active", "Inactive"],
            "ChurnRate": [active_churn, inactive_churn]
        })
        fig3 = px.bar(
            active_churn_df, x="Status", y="ChurnRate",
            text=active_churn_df["ChurnRate"].round(1).astype(str) + "%",
            title="Active vs Inactive Churn Rate",
            color="Status",
            color_discrete_map={"Active": "#2e7d32", "Inactive": "#c62828"},
        )
        fig3.update_traces(textposition="outside")
        fig3.update_layout(showlegend=False, yaxis_title="Churn Rate (%)")
        st.plotly_chart(fig3, use_container_width=True)

    with c4:
        geo_engagement = df.groupby(["Geography", "EngagementProfile"]).size().reset_index(name="Count")
        fig4 = px.bar(
            geo_engagement, x="Geography", y="Count", color="EngagementProfile",
            title="Engagement Profile Mix by Geography",
            barmode="stack",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        st.plotly_chart(fig4, use_container_width=True)

    st.info(
        "💡 **Insight:** Inactive customers churn at a substantially higher rate than active ones. "
        "Engagement — not balance or salary alone — is a leading indicator of churn risk."
    )

# ==========================================================================
# TAB 2 — Product Utilization Impact Analysis
# ==========================================================================
with tab2:
    st.subheader("Product Utilization Impact Analysis")

    c1, c2 = st.columns([1, 1])

    with c1:
        prod_churn = df.groupby("NumOfProducts")["Exited"].agg(["mean", "count"]).reset_index()
        prod_churn["mean"] = prod_churn["mean"] * 100
        fig5 = px.bar(
            prod_churn, x="NumOfProducts", y="mean",
            text=prod_churn["mean"].round(1).astype(str) + "%",
            title="Churn Rate by Number of Products",
            labels={"mean": "Churn Rate (%)", "NumOfProducts": "Number of Products"},
            color="mean",
            color_continuous_scale="Reds",
        )
        fig5.update_traces(textposition="outside")
        fig5.update_layout(coloraxis_showscale=False, yaxis_title="Churn Rate (%)")
        st.plotly_chart(fig5, use_container_width=True)

    with c2:
        df["ProductTier"] = np.where(df["NumOfProducts"] == 1, "Single-Product", "Multi-Product")
        tier_churn = df.groupby("ProductTier")["Exited"].agg(["mean", "count"]).reset_index()
        tier_churn["mean"] = tier_churn["mean"] * 100
        fig6 = px.bar(
            tier_churn, x="ProductTier", y="mean",
            text=tier_churn["mean"].round(1).astype(str) + "%",
            title="Single-Product vs Multi-Product Retention",
            color="ProductTier",
            color_discrete_sequence=["#c62828", "#2e7d32"],
        )
        fig6.update_traces(textposition="outside")
        fig6.update_layout(showlegend=False, yaxis_title="Churn Rate (%)")
        st.plotly_chart(fig6, use_container_width=True)

    c3, c4 = st.columns([1, 1])
    with c3:
        fig7 = px.box(
            df, x="NumOfProducts", y="Balance", color="ProductTier",
            title="Balance Distribution by Product Count",
            color_discrete_sequence=["#c62828", "#2e7d32"],
        )
        st.plotly_chart(fig7, use_container_width=True)

    with c4:
        prod_active = df.groupby(["NumOfProducts", "IsActiveMember"])["Exited"].mean().reset_index()
        prod_active["Exited"] = prod_active["Exited"] * 100
        prod_active["IsActiveMember"] = prod_active["IsActiveMember"].map({1: "Active", 0: "Inactive"})
        fig8 = px.line(
            prod_active, x="NumOfProducts", y="Exited", color="IsActiveMember",
            markers=True,
            title="Product Depth vs Churn, Split by Activity Status",
            labels={"Exited": "Churn Rate (%)", "NumOfProducts": "Number of Products"},
            color_discrete_map={"Active": "#2e7d32", "Inactive": "#c62828"},
        )
        st.plotly_chart(fig8, use_container_width=True)

    st.info(
        "💡 **Insight:** Customers with a single product churn at a notably higher rate than those holding "
        "two or more products, suggesting product depth strengthens retention — provided customers remain active."
    )

# ==========================================================================
# TAB 3 — High-Value Disengaged Customer Detector
# ==========================================================================
with tab3:
    st.subheader("High-Value Disengaged Customer Detector")
    st.caption("Identify premium customers (high balance/salary) who show signs of disengagement — the 'silent churn' risk pool.")

    f1, f2, f3 = st.columns(3)
    with f1:
        balance_pct = st.slider("Balance percentile threshold", 50, 99, 75, step=5)
    with f2:
        salary_pct = st.slider("Salary percentile threshold", 50, 99, 75, step=5)
    with f3:
        require_inactive = st.checkbox("Require inactive status", value=True)

    bal_thresh = df["Balance"].quantile(balance_pct / 100)
    sal_thresh = df["EstimatedSalary"].quantile(salary_pct / 100)

    condition = (df["Balance"] >= bal_thresh) | (df["EstimatedSalary"] >= sal_thresh)
    if require_inactive:
        condition &= (df["IsActiveMember"] == 0)

    at_risk = df[condition].copy()

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("At-Risk Premium Customers", f"{len(at_risk):,}", f"{len(at_risk)/len(df)*100:.1f}% of filtered base")
    with m2:
        st.metric("Churn Rate in This Segment", f"{at_risk['Exited'].mean()*100:.1f}%" if len(at_risk) else "—")
    with m3:
        st.metric("Avg. Balance in Segment", f"€{at_risk['Balance'].mean():,.0f}" if len(at_risk) else "—")

    c1, c2 = st.columns([1, 1])
    with c1:
        fig9 = px.scatter(
            df, x="Balance", y="EstimatedSalary", color="IsActiveMember",
            symbol="Exited",
            title="Balance vs Salary — Disengaged Premium Customers Highlighted",
            labels={"IsActiveMember": "Active"},
            color_continuous_scale="RdYlGn",
            opacity=0.6,
        )
        fig9.add_shape(type="line", x0=bal_thresh, x1=bal_thresh, y0=df["EstimatedSalary"].min(), y1=df["EstimatedSalary"].max(),
                        line=dict(color="orange", dash="dash"))
        fig9.add_shape(type="line", x0=df["Balance"].min(), x1=df["Balance"].max(), y0=sal_thresh, y1=sal_thresh,
                        line=dict(color="orange", dash="dash"))
        st.plotly_chart(fig9, use_container_width=True)

    with c2:
        geo_risk = at_risk.groupby("Geography").size().reset_index(name="Count") if len(at_risk) else pd.DataFrame({"Geography": [], "Count": []})
        fig10 = px.bar(
            geo_risk, x="Geography", y="Count",
            title="At-Risk Premium Customers by Geography",
            color="Geography",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        st.plotly_chart(fig10, use_container_width=True)

    st.markdown("##### At-Risk Customer Detail")
    display_cols = ["CustomerId", "Surname", "Geography", "Age", "Balance", "EstimatedSalary",
                     "NumOfProducts", "IsActiveMember", "Tenure", "Exited"]
    st.dataframe(
        at_risk[display_cols].sort_values("Balance", ascending=False).reset_index(drop=True),
        use_container_width=True,
        height=350,
    )

    st.info(
        "💡 **Insight:** This segment represents 'silent churn' risk — financially attractive customers "
        "whose low engagement makes them prime candidates for proactive relationship-management outreach."
    )

# ==========================================================================
# TAB 4 — Retention Strength Scoring
# ==========================================================================
with tab4:
    st.subheader("Retention Strength Scoring Panel")
    st.caption("Relationship Strength Index blends activity status, product depth, credit card ownership, and tenure into a single 0–100 score.")

    c1, c2 = st.columns([1, 1])
    with c1:
        fig11 = px.histogram(
            df, x="RelationshipStrengthIndex", color="Exited",
            nbins=30, barmode="overlay",
            title="Relationship Strength Index Distribution by Churn Status",
            labels={"Exited": "Churned"},
            color_discrete_sequence=["#2e7d32", "#c62828"],
        )
        st.plotly_chart(fig11, use_container_width=True)

    with c2:
        df["RSI_Bucket"] = pd.cut(
            df["RelationshipStrengthIndex"],
            bins=[0, 25, 50, 75, 100],
            labels=["0–25 (Weak)", "25–50 (Fragile)", "50–75 (Solid)", "75–100 (Sticky)"]
        )
        rsi_churn = df.groupby("RSI_Bucket")["Exited"].mean().reset_index()
        rsi_churn["Exited"] = rsi_churn["Exited"] * 100
        fig12 = px.bar(
            rsi_churn, x="RSI_Bucket", y="Exited",
            text=rsi_churn["Exited"].round(1).astype(str) + "%",
            title="Churn Rate by Relationship Strength Tier",
            labels={"Exited": "Churn Rate (%)", "RSI_Bucket": "Relationship Strength Tier"},
            color="RSI_Bucket",
            color_discrete_sequence=["#c62828", "#ef6c00", "#fbc02d", "#2e7d32"],
        )
        fig12.update_traces(textposition="outside")
        fig12.update_layout(showlegend=False)
        st.plotly_chart(fig12, use_container_width=True)

    c3, c4 = st.columns([1, 1])
    with c3:
        tenure_churn = df.groupby("Tenure")["Exited"].mean().reset_index()
        tenure_churn["Exited"] = tenure_churn["Exited"] * 100
        fig13 = px.line(
            tenure_churn, x="Tenure", y="Exited", markers=True,
            title="Churn Rate by Tenure (Years with Bank)",
            labels={"Exited": "Churn Rate (%)"},
        )
        st.plotly_chart(fig13, use_container_width=True)

    with c4:
        fig14 = px.scatter(
            df, x="RelationshipStrengthIndex", y="Balance", color="Exited",
            title="Relationship Strength vs Balance",
            color_discrete_sequence=["#2e7d32", "#c62828"],
            opacity=0.5,
        )
        st.plotly_chart(fig14, use_container_width=True)

    st.markdown("##### Sticky Customer Profile (Top Relationship Strength Tier)")
    sticky = df[df["RSI_Bucket"] == "75–100 (Sticky)"]
    if len(sticky):
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Customers", f"{len(sticky):,}")
        s2.metric("Churn Rate", f"{sticky['Exited'].mean()*100:.1f}%")
        s3.metric("Avg. Products", f"{sticky['NumOfProducts'].mean():.1f}")
        s4.metric("Avg. Tenure", f"{sticky['Tenure'].mean():.1f} yrs")
    else:
        st.write("No customers fall into this tier under current filters.")

    st.info(
        "💡 **Insight:** Customers in the top Relationship Strength tier churn at a far lower rate, "
        "confirming that combined engagement and product depth — not any single factor — drives durable retention."
    )

st.markdown("---")
st.caption("European Central Bank · Customer Engagement & Product Utilization Analytics for Retention Strategy · Prepared via Unified Mentor Analytics Program")
