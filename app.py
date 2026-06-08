import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import random
import time

from langgraph.graph import StateGraph, END

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Financial Crime SOC",
    layout="wide"
)

st.title("🏦 Real-Time Financial Crime SOC (Agentic + LangGraph + HITL)")

# =========================================================
# SESSION STATE
# =========================================================

if "results" not in st.session_state:
    st.session_state.results = []

if "alerts" not in st.session_state:
    st.session_state.alerts = []

if "stats" not in st.session_state:
    st.session_state.stats = {
        "APPROVE": 0,
        "REVIEW": 0,
        "BLOCK": 0
    }

if "customer_memory" not in st.session_state:
    st.session_state.customer_memory = {}

if "investigator_actions" not in st.session_state:
    st.session_state.investigator_actions = {}

# =========================================================
# DATA GENERATOR
# =========================================================

def generate_transaction(i):

    return {
        "txn_id": f"T{i}",
        "customer_id": f"C{random.randint(100,120)}",
        "amount": random.randint(100, 20000),
        "velocity": random.randint(1, 12),
        "country_risk": random.choice([0, 1]),
        "device_change": random.choice([0, 1])
    }

# =========================================================
# SAMPLE DATAFRAME
# =========================================================

df = pd.DataFrame([
    generate_transaction(i)
    for i in range(50)
])

# =========================================================
# CUSTOMER MEMORY
# =========================================================

def update_customer_memory(txn, decision):

    cid = txn["customer_id"]

    if cid not in st.session_state.customer_memory:

        st.session_state.customer_memory[cid] = {
            "txn_count": 0,
            "blocked_count": 0,
            "total_amount": 0
        }

    st.session_state.customer_memory[cid]["txn_count"] += 1

    st.session_state.customer_memory[cid]["total_amount"] += txn["amount"]

    if decision == "BLOCK":

        st.session_state.customer_memory[cid]["blocked_count"] += 1

# =========================================================
# FRAUD AGENT
# =========================================================

def fraud_agent(state):

    risk = 0
    reasons = []

    if state["amount"] > 15000:

        risk += 0.4
        reasons.append("High Amount Spike")

    if state["device_change"] == 1:

        risk += 0.2
        reasons.append("Device Change Detected")

    return {
        **state,
        "fraud_score": risk,
        "reasons": reasons
    }

# =========================================================
# AML AGENT
# =========================================================

def aml_agent(state):

    risk = 0

    reasons = state.get("reasons", [])

    if state["velocity"] > 8:

        risk += 0.4
        reasons.append("Velocity Breach")

    if state["country_risk"] == 1:

        risk += 0.2
        reasons.append("High Risk Geography")

    return {
        **state,
        "aml_score": risk,
        "reasons": reasons
    }

# =========================================================
# BEHAVIORAL AGENT
# =========================================================

def behavioral_agent(state):

    cid = state["customer_id"]

    risk = 0

    reasons = state.get("reasons", [])

    memory = st.session_state.customer_memory

    if cid in memory:

        avg_amount = (
            memory[cid]["total_amount"] /
            max(memory[cid]["txn_count"], 1)
        )

        if state["amount"] > avg_amount * 3:

            risk += 0.3
            reasons.append("Behavioral Anomaly")

        if memory[cid]["blocked_count"] >= 2:

            risk += 0.3
            reasons.append("Repeat Risk Customer")

    return {
        **state,
        "behavior_score": risk,
        "reasons": reasons
    }

# =========================================================
# DECISION AGENT
# =========================================================

def decision_agent(state):

    total_risk = (
        state.get("fraud_score", 0)
        + state.get("aml_score", 0)
        + state.get("behavior_score", 0)
    )

    if total_risk >= 0.8:

        decision = "BLOCK"

    elif total_risk >= 0.45:

        decision = "REVIEW"

    else:

        decision = "APPROVE"

    return {
        **state,
        "risk_score": round(total_risk, 2),
        "decision": decision,
        "reasons": state.get("reasons", [])
    }

# =========================================================
# LANGGRAPH
# =========================================================

workflow = StateGraph(dict)

workflow.add_node("fraud", fraud_agent)
workflow.add_node("aml", aml_agent)
workflow.add_node("behavior", behavioral_agent)
workflow.add_node("decision", decision_agent)

workflow.set_entry_point("fraud")

workflow.add_edge("fraud", "aml")
workflow.add_edge("aml", "behavior")
workflow.add_edge("behavior", "decision")
workflow.add_edge("decision", END)

app = workflow.compile()

# =========================================================
# METRICS
# =========================================================

col1, col2, col3 = st.columns(3)

metric1 = col1.empty()
metric2 = col2.empty()
metric3 = col3.empty()

metric1.metric("TOTAL", 0)
metric2.metric("BLOCK", 0)
metric3.metric("REVIEW", 0)

# =========================================================
# LIVE STREAM
# =========================================================

st.subheader("🚨 Live Feed")

feed_placeholder = st.empty()

live_feed = []

# =========================================================
# STREAM ENGINE
# =========================================================

for i in range(len(df)):

    txn = df.iloc[i].to_dict()

    result = app.invoke(txn)

    decision = result["decision"]

    risk = result["risk_score"]

    reasons = result["reasons"]

    # =====================================================
    # UPDATE MEMORY
    # =====================================================

    update_customer_memory(txn, decision)

    # =====================================================
    # STORE RESULT
    # =====================================================

    st.session_state.results.append({
        "txn_id": txn["txn_id"],
        "decision": decision,
        "risk": risk,
        "reasons": reasons,
        "customer": txn["customer_id"]
    })

    # =====================================================
    # COUNTERS
    # =====================================================

    if decision not in st.session_state.stats:

        st.session_state.stats[decision] = 0

    st.session_state.stats[decision] += 1

    # =====================================================
    # ALERT CARD
    # =====================================================

    if decision == "BLOCK":

        icon = "🚨"
        color = "red"

    elif decision == "REVIEW":

        icon = "⚠️"
        color = "orange"

    else:

        icon = "🟢"
        color = "green"

    reason_text = " | ".join(reasons)

    alert_html = f"""
    <div style="
        padding:12px;
        border-radius:10px;
        margin-bottom:10px;
        background-color:#111111;
        border-left:6px solid {color};
    ">
    <h4>{icon} {decision} | {txn['txn_id']} | Risk={risk}</h4>
    <p><b>Reasons:</b> {reason_text}</p>
    <p><b>Amount:</b> ₹{txn['amount']}</p>
    <p><b>Customer:</b> {txn['customer_id']}</p>
    </div>
    """

    live_feed.insert(0, alert_html)

    # =====================================================
    # REAL-TIME FEED UPDATE
    # =====================================================

    feed_placeholder.markdown(
        "".join(live_feed[:12]),
        unsafe_allow_html=True
    )

    # =====================================================
    # LIVE METRICS UPDATE
    # =====================================================

    metric1.metric(
        "TOTAL",
        len(st.session_state.results)
    )

    metric2.metric(
        "BLOCK",
        st.session_state.stats["BLOCK"]
    )

    metric3.metric(
        "REVIEW",
        st.session_state.stats["REVIEW"]
    )

    # =====================================================
    # HUMAN ACTIONS
    # =====================================================

    unique_key = f"{txn['txn_id']}_{time.time_ns()}"

    colA, colB = st.columns(2)

    with colA:

        if st.button(
            f"Freeze {txn['txn_id']}",
            key=f"freeze_{unique_key}"
        ):

            st.session_state.investigator_actions[
                txn["txn_id"]
            ] = "ACCOUNT FROZEN"

    with colB:

        if st.button(
            f"Escalate {txn['txn_id']}",
            key=f"escalate_{unique_key}"
        ):

            st.session_state.investigator_actions[
                txn["txn_id"]
            ] = "ESCALATED"

    # =====================================================
    # STREAM SPEED
    # =====================================================

    time.sleep(0.7)

# =========================================================
# INVESTIGATOR ACTIONS
# =========================================================

st.subheader("📌 Investigator Actions")

st.write(st.session_state.investigator_actions)

# =========================================================
# CUSTOMER RISK TABLE
# =========================================================

st.subheader("📊 High Risk Customers")

rows = []

for cid, mem in st.session_state.customer_memory.items():

    avg_amt = (
        mem["total_amount"] /
        max(mem["txn_count"], 1)
    )

    rows.append({
        "customer_id": cid,
        "txn_count": mem["txn_count"],
        "blocked_count": mem["blocked_count"],
        "avg_amount": round(avg_amt, 2)
    })

risk_df = pd.DataFrame(rows)

if not risk_df.empty:

    risk_df = risk_df.sort_values(
        by="blocked_count",
        ascending=False
    )

    st.dataframe(
        risk_df,
        width="stretch"
    )

# =========================================================
# ANALYTICS
# =========================================================

st.subheader("📈 Decision Analytics")

analytics_df = pd.DataFrame(st.session_state.results)

if not analytics_df.empty:

    chart_df = (
        analytics_df["decision"]
        .value_counts()
        .reset_index()
    )

    chart_df.columns = ["Decision", "Count"]

    fig = px.bar(
        chart_df,
        x="Decision",
        y="Count",
        title="Alert Distribution"
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )

# =========================================================
# COMPLETED
# =========================================================

st.success("✅ Live Agentic Stream Completed")
