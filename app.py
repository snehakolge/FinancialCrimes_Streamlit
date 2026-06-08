import streamlit as st
import pandas as pd
import numpy as np
import random
import time
from datetime import datetime
from langgraph.graph import StateGraph, END
import plotly.express as px

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

if "running" not in st.session_state:
    st.session_state.running = False

if "transactions" not in st.session_state:
    st.session_state.transactions = []

if "alerts" not in st.session_state:
    st.session_state.alerts = []

if "customer_memory" not in st.session_state:
    st.session_state.customer_memory = {}

if "stats" not in st.session_state:
    st.session_state.stats = {
        "APPROVE": 0,
        "REVIEW": 0,
        "BLOCK": 0,
        "FREEZE": 0
    }

if "investigator_actions" not in st.session_state:
    st.session_state.investigator_actions = {}

# =========================================================
# GENERATE TRANSACTION
# =========================================================

def generate_transaction(i):

    customer_id = f"C{random.randint(100,120)}"

    txn = {
        "txn_id": f"T{i}",
        "customer_id": customer_id,
        "amount": random.randint(500, 20000),
        "velocity": random.randint(1, 15),
        "device_change": random.choice([0, 1]),
        "geo_risk": random.choice([0, 1]),
        "behavioral_anomaly": random.choice([0, 1]),
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }

    return txn

# =========================================================
# LANGGRAPH AGENTS
# =========================================================

def amount_agent(state):

    amount = state.get("amount", 0)

    reasons = state.get("reasons", [])
    risk = state.get("risk_score", 0)

    if amount > 12000:
        risk += 0.4
        reasons.append("High Amount Spike")

    return {
        **state,
        "risk_score": risk,
        "reasons": reasons
    }

def velocity_agent(state):

    velocity = state.get("velocity", 0)

    reasons = state.get("reasons", [])
    risk = state.get("risk_score", 0)

    if velocity > 8:
        risk += 0.3
        reasons.append("Velocity Breach")

    return {
        **state,
        "risk_score": risk,
        "reasons": reasons
    }

def device_agent(state):

    device_change = state.get("device_change", 0)

    reasons = state.get("reasons", [])
    risk = state.get("risk_score", 0)

    if device_change == 1:
        risk += 0.2
        reasons.append("Device Change Detected")

    return {
        **state,
        "risk_score": risk,
        "reasons": reasons
    }

def geo_agent(state):

    geo_risk = state.get("geo_risk", 0)

    reasons = state.get("reasons", [])
    risk = state.get("risk_score", 0)

    if geo_risk == 1:
        risk += 0.2
        reasons.append("High Risk Geography")

    return {
        **state,
        "risk_score": risk,
        "reasons": reasons
    }

def behavior_agent(state):

    anomaly = state.get("behavioral_anomaly", 0)

    reasons = state.get("reasons", [])
    risk = state.get("risk_score", 0)

    if anomaly == 1:
        risk += 0.3
        reasons.append("Behavioral Anomaly")

    return {
        **state,
        "risk_score": risk,
        "reasons": reasons
    }

def historical_agent(state):

    customer = state.get("customer_id")

    reasons = state.get("reasons", [])
    risk = state.get("risk_score", 0)

    customer_memory = st.session_state.customer_memory

    if customer not in customer_memory:
        customer_memory[customer] = 0

    if customer_memory[customer] >= 2:
        risk += 0.2
        reasons.append("Repeat Risk Customer")

    return {
        **state,
        "risk_score": risk,
        "reasons": reasons
    }

def decision_agent(state):

    risk = state.get("risk_score", 0)

    if risk >= 1.2:
        decision = "FREEZE"
        action = "Freeze Customer Account"

    elif risk >= 0.8:
        decision = "BLOCK"
        action = "Block Transaction"

    elif risk >= 0.5:
        decision = "REVIEW"
        action = "Send To Analyst Queue"

    else:
        decision = "APPROVE"
        action = "Approve Transaction"

    state["decision"] = decision
    state["action"] = action

    customer = state["customer_id"]

    if decision in ["BLOCK", "FREEZE", "REVIEW"]:
        st.session_state.customer_memory[customer] += 1

    return state

# =========================================================
# BUILD LANGGRAPH
# =========================================================

workflow = StateGraph(dict)

workflow.add_node("amount_agent", amount_agent)
workflow.add_node("velocity_agent", velocity_agent)
workflow.add_node("device_agent", device_agent)
workflow.add_node("geo_agent", geo_agent)
workflow.add_node("behavior_agent", behavior_agent)
workflow.add_node("historical_agent", historical_agent)
workflow.add_node("decision_agent", decision_agent)

workflow.set_entry_point("amount_agent")

workflow.add_edge("amount_agent", "velocity_agent")
workflow.add_edge("velocity_agent", "device_agent")
workflow.add_edge("device_agent", "geo_agent")
workflow.add_edge("geo_agent", "behavior_agent")
workflow.add_edge("behavior_agent", "historical_agent")
workflow.add_edge("historical_agent", "decision_agent")
workflow.add_edge("decision_agent", END)

app = workflow.compile()

# =========================================================
# CONTROL BUTTONS
# =========================================================

col1, col2 = st.columns(2)

with col1:
    if st.button("▶ Start Live Stream"):
        st.session_state.running = True

with col2:
    if st.button("⏹ Stop Stream"):
        st.session_state.running = False

# =========================================================
# KPI METRICS
# =========================================================

m1, m2, m3, m4 = st.columns(4)

m1.metric("TOTAL", len(st.session_state.transactions))
m2.metric("BLOCK", st.session_state.stats["BLOCK"])
m3.metric("REVIEW", st.session_state.stats["REVIEW"])
m4.metric("FREEZE", st.session_state.stats["FREEZE"])

# =========================================================
# LIVE FEED PLACEHOLDER
# =========================================================

feed = st.empty()

# =========================================================
# STREAMING ENGINE
# =========================================================

if st.session_state.running:

    for i in range(50):

        if not st.session_state.running:
            break

        txn = generate_transaction(i)

        initial_state = {
            **txn,
            "risk_score": 0,
            "reasons": []
        }

        result = app.invoke(initial_state)

        decision = result["decision"]
        risk = round(result["risk_score"], 2)

        st.session_state.stats[decision] += 1

        transaction_record = {
            "txn_id": txn["txn_id"],
            "customer_id": txn["customer_id"],
            "amount": txn["amount"],
            "decision": decision,
            "risk_score": risk,
            "reasons": result["reasons"],
            "timestamp": txn["timestamp"],
            "action": result["action"]
        }

        st.session_state.transactions.append(transaction_record)

        if decision in ["BLOCK", "FREEZE", "REVIEW"]:
            st.session_state.alerts.append(transaction_record)

        # =====================================================
        # LIVE FEED
        # =====================================================

        with feed.container():

            st.subheader("🚨 Live Feed")

            latest = st.session_state.transactions[-12:]

            for r in reversed(latest):

                if r["decision"] == "FREEZE":
                    emoji = "🧊"

                elif r["decision"] == "BLOCK":
                    emoji = "🚨"

                elif r["decision"] == "REVIEW":
                    emoji = "⚠️"

                else:
                    emoji = "🟢"

                st.markdown(
                    f"""
### {emoji} {r['decision']} | {r['txn_id']} | Risk={r['risk_score']}

**Reasons:** {" | ".join(r['reasons'])}

**Action:** {r['action']}

**Amount:** ₹{r['amount']}

**Customer:** {r['customer_id']}
"""
                )

        time.sleep(1)

    st.success("✅ Live Agentic Stream Completed")

# =========================================================
# INVESTIGATOR ACTIONS
# =========================================================

st.subheader("📌 Investigator Actions")

high_risk = [
    x for x in st.session_state.transactions
    if x["decision"] in ["BLOCK", "FREEZE", "REVIEW"]
]

for idx, r in enumerate(high_risk[-5:]):

    c1, c2, c3 = st.columns([4, 1, 1])

    with c1:
        st.write(
            f"{r['txn_id']} | {r['customer_id']} | {r['decision']} | Risk={r['risk_score']}"
        )

    with c2:
        if st.button("Approve", key=f"approve_{idx}_{r['txn_id']}"):

            st.session_state.investigator_actions[r["txn_id"]] = "Approved By Analyst"

    with c3:
        if st.button("Escalate", key=f"escalate_{idx}_{r['txn_id']}"):

            st.session_state.investigator_actions[r["txn_id"]] = "Escalated To SOC Manager"

st.write(st.session_state.investigator_actions)

# =========================================================
# HIGH RISK CUSTOMERS
# =========================================================

st.subheader("📊 High Risk Customers")

risk_df = pd.DataFrame(
    list(st.session_state.customer_memory.items()),
    columns=["Customer", "Risk Alerts"]
)

if len(risk_df) > 0:

    risk_df = risk_df.sort_values(
        by="Risk Alerts",
        ascending=False
    )

    st.dataframe(risk_df)

# =========================================================
# ANALYTICS
# =========================================================

st.subheader("📈 Decision Analytics")

stats_df = pd.DataFrame({
    "Decision": list(st.session_state.stats.keys()),
    "Count": list(st.session_state.stats.values())
})

fig = px.bar(
    stats_df,
    x="Decision",
    y="Count",
    title="Fraud Decision Distribution"
)

st.plotly_chart(fig, use_container_width=True)

# =========================================================
# CASE MANAGEMENT TABLE
# =========================================================

st.subheader("🗂 Case Management Queue")

if len(st.session_state.transactions) > 0:

    case_df = pd.DataFrame(st.session_state.transactions)

    st.dataframe(
        case_df.tail(20),
        use_container_width=True
    )
