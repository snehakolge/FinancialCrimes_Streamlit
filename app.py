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
# TRANSACTION GENERATOR
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
# AGENTS
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

total_txns = (
    st.session_state.stats["APPROVE"]
    + st.session_state.stats["REVIEW"]
    + st.session_state.stats["BLOCK"]
)

col1.metric("TOTAL", total_txns)
col2.metric("BLOCK", st.session_state.stats["BLOCK"])
col3.metric("REVIEW", st.session_state.stats["REVIEW"])

# =========================================================
# LIVE FEED
# =========================================================

st.subheader("🚨 Live Feed")

feed_placeholder = st.empty()

# =========================================================
# STREAMING
# =========================================================

for i in range(50):

    txn = generate_transaction(i)

    result = app.invoke(txn)

    decision = result["decision"]

    risk = result["risk_score"]

    reasons = result["reasons"]

    update_customer_memory(txn, decision)

    if decision not in st.session_state.stats:

        st.session_state.stats[decision] = 0

    st.session_state.stats[decision] += 1

    alert = {
        "txn_id": txn["txn_id"],
        "customer_id": txn["customer_id"],
        "decision": decision,
        "risk": risk,
        "reasons": reasons
    }

    st.session_state.alerts.insert(0, alert)

    st.session_state.alerts = st.session_state.alerts[:15]

    with feed_placeholder.container():

        for idx, alert in enumerate(st.session_state.alerts):

            txn_id = alert["txn_id"]

            decision = alert["decision"]

            risk = alert["risk"]

            reasons = alert["reasons"]

            reason_text = " | ".join(reasons)

            if decision == "BLOCK":

                st.error(
                    f"🚨 BLOCK | {txn_id} | Risk={risk}\n\nReasons: {reason_text}"
                )

            elif decision == "REVIEW":

                st.warning(
                    f"⚠️ REVIEW | {txn_id} | Risk={risk}\n\nReasons: {reason_text}"
                )

            else:

                st.success(
                    f"🟢 APPROVE | {txn_id} | Risk={risk}"
                )

            # UNIQUE BUTTON KEYS

            unique_id = f"{txn_id}_{idx}_{i}_{time.time()}"

            colA, colB = st.columns(2)

            with colA:

                if st.button(
                    f"Freeze {txn_id}",
                    key=f"freeze_{unique_id}"
                ):

                    st.session_state.investigator_actions[
                        txn_id
                    ] = "ACCOUNT FROZEN"

            with colB:

                if st.button(
                    f"Escalate {txn_id}",
                    key=f"escalate_{unique_id}"
                ):

                    st.session_state.investigator_actions[
                        txn_id
                    ] = "ESCALATED"

    time.sleep(0.15)

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

analytics_df = pd.DataFrame(st.session_state.alerts)

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
# COMPLETE
# =========================================================

st.success("✅ Live Agentic Stream Completed")
