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
# GENERATE LIVE DATA
# =========================================================

def generate_transaction(i):

    customer_id = f"C{random.randint(100,120)}"

    return {
        "txn_id": f"T{i}",
        "customer_id": customer_id,
        "amount": random.randint(100, 20000),
        "velocity": random.randint(1, 12),
        "country_risk": random.choice([0, 1]),
        "device_change": random.choice([0, 1]),
    }

# =========================================================
# MEMORY UPDATE
# =========================================================

def update_customer_memory(txn, decision):

    cid = txn["customer_id"]

    memory = st.session_state.customer_memory

    if cid not in memory:
        memory[cid] = {
            "txn_count": 0,
            "blocked_count": 0,
            "total_amount": 0
        }

    memory[cid]["txn_count"] += 1
    memory[cid]["total_amount"] += txn["amount"]

    if decision == "BLOCK":
        memory[cid]["blocked_count"] += 1

# =========================================================
# LANGGRAPH AGENTS
# =========================================================

def fraud_agent(state):

    risk = 0
    reasons = []

    amount = state["amount"]

    if amount > 15000:
        risk += 0.4
        reasons.append("High Amount Spike")

    if state["device_change"] == 1:
        risk += 0.2
        reasons.append("Device Change Detected")

    return {
        "fraud_score": risk,
        "reasons": reasons
    }

def aml_agent(state):

    risk = 0
    reasons = state.get("reasons", [])

    velocity = state["velocity"]

    if velocity > 8:
        risk += 0.4
        reasons.append("Velocity Breach")

    if state["country_risk"] == 1:
        risk += 0.2
        reasons.append("High Risk Geography")

    return {
        "aml_score": risk,
        "reasons": reasons
    }

def behavioral_agent(state):

    cid = state["customer_id"]

    memory = st.session_state.customer_memory

    risk = 0
    reasons = state.get("reasons", [])

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
        "behavior_score": risk,
        "reasons": reasons
    }

def decision_agent(state):

    total_risk = (
        state.get("fraud_score", 0) +
        state.get("aml_score", 0) +
        state.get("behavior_score", 0)
    )

    if total_risk >= 0.8:
        decision = "BLOCK"

    elif total_risk >= 0.45:
        decision = "REVIEW"

    else:
        decision = "APPROVE"

    return {
        "risk_score": round(total_risk, 2),
        "decision": decision,
        "reasons": state.get("reasons", [])
    }

# =========================================================
# BUILD GRAPH
# =========================================================

graph = StateGraph(dict)

graph.add_node("fraud", fraud_agent)
graph.add_node("aml", aml_agent)
graph.add_node("behavior", behavioral_agent)
graph.add_node("decision", decision_agent)

graph.set_entry_point("fraud")

graph.add_edge("fraud", "aml")
graph.add_edge("aml", "behavior")
graph.add_edge("behavior", "decision")
graph.add_edge("decision", END)

app = graph.compile()

# =========================================================
# DASHBOARD METRICS
# =========================================================

col1, col2, col3 = st.columns(3)

metric_total = (
    st.session_state.stats["APPROVE"] +
    st.session_state.stats["REVIEW"] +
    st.session_state.stats["BLOCK"]
)

col1.metric("TOTAL", metric_total)
col2.metric("BLOCK", st.session_state.stats["BLOCK"])
col3.metric("REVIEW", st.session_state.stats["REVIEW"])

# =========================================================
# LIVE STREAM SECTION
# =========================================================

st.subheader("🚨 Live Feed")

feed_placeholder = st.empty()

# =========================================================
# LIVE TRANSACTION STREAM
# =========================================================

for i in range(50):

    txn = generate_transaction(i)

    result = app.invoke(txn)

    decision = result["decision"]
    risk = result["risk_score"]
    reasons = result["reasons"]

    update_customer_memory(txn, decision)

    st.session_state.stats[decision] += 1

    alert = {
        "txn_id": txn["txn_id"],
        "customer_id": txn["customer_id"],
        "decision": decision,
        "risk_score": risk,
        "reasons": reasons
    }

    st.session_state.alerts.insert(0, alert)

    # KEEP LAST 15 ALERTS
    st.session_state.alerts = st.session_state.alerts[:15]

    with feed_placeholder.container():

        for idx, a in enumerate(st.session_state.alerts):

            if a["decision"] == "BLOCK":

                st.error(
                    f"""
🚨 BLOCK | {a['txn_id']} | Risk={a['risk_score']}

Reasons:
- {' | '.join(a['reasons'])}
"""
                )

            elif a["decision"] == "REVIEW":

                st.warning(
                    f"""
⚠️ REVIEW | {a['txn_id']} | Risk={a['risk_score']}

Reasons:
- {' | '.join(a['reasons'])}
"""
                )

            else:

                st.success(
                    f"""
🟢 APPROVE | {a['txn_id']} | Risk={a['risk_score']}
"""
                )

            # UNIQUE BUTTON KEYS
            unique_key = f"{a['txn_id']}_{idx}_{time.time()}"

            colA, colB = st.columns(2)

            with colA:

                if st.button(
                    f"Freeze {a['txn_id']}",
                    key=f"freeze_{unique_key}"
                ):
                    st.session_state.investigator_actions[
                        a["txn_id"]
                    ] = "ACCOUNT FROZEN"

            with colB:

                if st.button(
                    f"Escalate {a['txn_id']}",
                    key=f"escalate_{unique_key}"
                ):
                    st.session_state.investigator_actions[
                        a["txn_id"]
                    ] = "ESCALATED"

    time.sleep(0.15)

# =========================================================
# INVESTIGATOR LOG
# =========================================================

st.subheader("📌 Investigator Actions")

st.write(st.session_state.investigator_actions)

# =========================================================
# HIGH RISK CUSTOMERS
# =========================================================

st.subheader("📊 High Risk Customers")

risk_rows = []

for cid, mem in st.session_state.customer_memory.items():

    risk_rows.append({
        "customer_id": cid,
        "txn_count": mem["txn_count"],
        "blocked_count": mem["blocked_count"],
        "avg_amount":
            round(mem["total_amount"] / mem["txn_count"], 2)
    })

risk_df = pd.DataFrame(risk_rows)

if not risk_df.empty:

    st.dataframe(
        risk_df.sort_values(
            by="blocked_count",
            ascending=False
        ),
        width="stretch"
    )

# =========================================================
# RISK TREND CHART
# =========================================================

st.subheader("📈 Decision Analytics")

analytics_df = pd.DataFrame(st.session_state.alerts)

if not analytics_df.empty:

    chart = (
        analytics_df["decision"]
        .value_counts()
        .reset_index()
    )

    chart.columns = ["Decision", "Count"]

    fig = px.bar(
        chart,
        x="Decision",
        y="Count",
        title="Alert Distribution"
    )

    st.plotly_chart(fig, width="stretch")

# =========================================================
# END
# =========================================================

st.success("✅ Live Agentic Stream Completed")
