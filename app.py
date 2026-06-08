import streamlit as st
import pandas as pd
import random
import time

from typing import TypedDict
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

if "stats" not in st.session_state:
    st.session_state.stats = {
        "APPROVE": 0,
        "REVIEW": 0,
        "BLOCK": 0,
        "FREEZE": 0
    }

# FIX OLD SESSION STATES
if "FREEZE" not in st.session_state.stats:
    st.session_state.stats["FREEZE"] = 0

if "alerts" not in st.session_state:
    st.session_state.alerts = []

if "running" not in st.session_state:
    st.session_state.running = False

if "txn_counter" not in st.session_state:
    st.session_state.txn_counter = 0

if "customer_risk" not in st.session_state:
    st.session_state.customer_risk = {}

if "actions" not in st.session_state:
    st.session_state.actions = {}

# =========================================================
# METRICS
# =========================================================

m1, m2, m3, m4 = st.columns(4)

m1.metric(
    "TOTAL",
    sum(st.session_state.stats.values())
)

m2.metric(
    "BLOCK",
    st.session_state.stats["BLOCK"]
)

m3.metric(
    "REVIEW",
    st.session_state.stats["REVIEW"]
)

m4.metric(
    "FREEZE",
    st.session_state.stats["FREEZE"]
)

# =========================================================
# TRANSACTION GENERATOR
# =========================================================

def generate_transaction():

    txn_id = f"T{st.session_state.txn_counter}"
    st.session_state.txn_counter += 1

    customer_id = f"C{random.randint(100,120)}"

    txn = {
        "txn_id": txn_id,
        "customer_id": customer_id,
        "amount": random.randint(100, 20000),
        "velocity": random.randint(1, 15),
        "device_change": random.choice([0,1]),
        "geo_risk": random.choice([0,1]),
        "behavioral_anomaly": random.choice([0,1]),
        "risk_score": 0,
        "reasons": []
    }

    return txn

# =========================================================
# LANGGRAPH STATE
# =========================================================

class FraudState(TypedDict):
    txn_id: str
    customer_id: str
    amount: int
    velocity: int
    device_change: int
    geo_risk: int
    behavioral_anomaly: int
    risk_score: float
    reasons: list
    decision: str

# =========================================================
# AGENTS
# =========================================================

def amount_agent(state):

    if state.get("amount",0) > 12000:
        state["risk_score"] += 0.4
        state["reasons"].append("High Amount Spike")

    return state

def velocity_agent(state):

    if state.get("velocity",0) > 8:
        state["risk_score"] += 0.3
        state["reasons"].append("Velocity Breach")

    return state

def device_agent(state):

    if state.get("device_change",0) == 1:
        state["risk_score"] += 0.2
        state["reasons"].append("Device Change Detected")

    return state

def geo_agent(state):

    if state.get("geo_risk",0) == 1:
        state["risk_score"] += 0.2
        state["reasons"].append("High Risk Geography")

    return state

def behavior_agent(state):

    if state.get("behavioral_anomaly",0) == 1:
        state["risk_score"] += 0.2
        state["reasons"].append("Behavioral Anomaly")

    return state

def memory_agent(state):

    customer = state.get("customer_id")

    old_risk = st.session_state.customer_risk.get(customer, 0)

    if old_risk > 2:
        state["risk_score"] += 0.2
        state["reasons"].append("Repeat Risk Customer")

    st.session_state.customer_risk[customer] = old_risk + 1

    return state

# =========================================================
# DECISION ENGINE
# =========================================================

def decision_agent(state):

    risk = state["risk_score"]

    if risk >= 1.2:
        decision = "FREEZE"

    elif risk >= 0.8:
        decision = "BLOCK"

    elif risk >= 0.5:
        decision = "REVIEW"

    else:
        decision = "APPROVE"

    state["decision"] = decision

    return state

# =========================================================
# LANGGRAPH BUILD
# =========================================================

workflow = StateGraph(FraudState)

workflow.add_node("amount", amount_agent)
workflow.add_node("velocity", velocity_agent)
workflow.add_node("device", device_agent)
workflow.add_node("geo", geo_agent)
workflow.add_node("behavior", behavior_agent)
workflow.add_node("memory", memory_agent)
workflow.add_node("decision", decision_agent)

workflow.set_entry_point("amount")

workflow.add_edge("amount", "velocity")
workflow.add_edge("velocity", "device")
workflow.add_edge("device", "geo")
workflow.add_edge("geo", "behavior")
workflow.add_edge("behavior", "memory")
workflow.add_edge("memory", "decision")
workflow.add_edge("decision", END)

app = workflow.compile()

# =========================================================
# BUTTONS
# =========================================================

c1, c2 = st.columns(2)

with c1:
    if st.button("▶ Start Live Stream"):
        st.session_state.running = True

with c2:
    if st.button("⏹ Stop Stream"):
        st.session_state.running = False

# =========================================================
# LIVE FEED
# =========================================================

feed_placeholder = st.empty()

if st.session_state.running:

    with feed_placeholder.container():

        st.subheader("🚨 Live Feed")

        for i in range(50):

            if not st.session_state.running:
                break

            txn = generate_transaction()

            result = app.invoke(txn)

            decision = result["decision"]

            st.session_state.stats[decision] += 1

            st.session_state.alerts.insert(0, result)

            emoji = {
                "APPROVE":"🟢",
                "REVIEW":"⚠️",
                "BLOCK":"🚨",
                "FREEZE":"🧊"
            }

            st.markdown(
                f"""
### {emoji[decision]} {decision} | {result['txn_id']} | Risk={round(result['risk_score'],2)}

**Reasons:** {' | '.join(result['reasons'])}

**Amount:** ₹{result['amount']}

**Customer:** {result['customer_id']}
                """
            )

            if decision in ["REVIEW","BLOCK","FREEZE"]:

                key = f"{result['txn_id']}_{i}_{decision}"

                if st.button(
                    f"Take Action {result['txn_id']}",
                    key=key
                ):
                    st.session_state.actions[result["txn_id"]] = "Investigated"

            time.sleep(0.5)

        st.success("✅ Live Agentic Stream Completed")

# =========================================================
# INVESTIGATOR ACTIONS
# =========================================================

st.subheader("📌 Investigator Actions")

st.write(st.session_state.actions)

# =========================================================
# HIGH RISK CUSTOMERS
# =========================================================

st.subheader("📊 High Risk Customers")

risk_df = pd.DataFrame(
    list(st.session_state.customer_risk.items()),
    columns=["Customer","Risk Count"]
)

if not risk_df.empty:
    st.dataframe(
        risk_df.sort_values(
            by="Risk Count",
            ascending=False
        ).head(10)
    )

# =========================================================
# DECISION ANALYTICS
# =========================================================

st.subheader("📈 Decision Analytics")

chart_df = pd.DataFrame({
    "Decision": list(st.session_state.stats.keys()),
    "Count": list(st.session_state.stats.values())
})

st.bar_chart(
    chart_df.set_index("Decision")
)
