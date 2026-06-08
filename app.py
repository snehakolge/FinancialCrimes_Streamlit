import streamlit as st
import pandas as pd
import random
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

# ---------------- STREAMLIT ----------------
st.set_page_config(page_title="Financial Crime SOC", layout="wide")
st.title("🏦 Real-Time Financial Crime Intelligence Platform (Agentic)")

# ---------------- SYNTHETIC DATA ----------------
def generate_data(n=200):
    data = []
    for i in range(n):
        data.append({
            "transaction_id": f"T{i}",
            "customer_id": f"C{random.randint(1000,1100)}",
            "amount": random.randint(100, 120000),
            "velocity_7d": random.randint(1, 50),
            "failed_txn_flag": random.randint(0, 1),
            "merchant_risk": round(random.uniform(0.1, 0.9), 2),
        })
    return pd.DataFrame(data)

# ---------------- STATE ----------------
class State(TypedDict):
    transaction: dict
    fraud_score: float
    aml_score: float
    rbi_flags: List[str]
    risk_score: float
    decision: str

# ---------------- AGENTS ----------------

def fraud_agent(state: State):
    t = state["transaction"]
    score = 0

    if t["amount"] > 50000:
        score += 0.4
    if t["velocity_7d"] > 30:
        score += 0.3
    if t["failed_txn_flag"] == 1:
        score += 0.2

    return {"fraud_score": min(score, 1.0)}


def aml_agent(state: State):
    t = state["transaction"]
    score = 0

    if t["amount"] < 3000:
        score += 0.5
    if t["merchant_risk"] > 0.6:
        score += 0.3

    return {"aml_score": min(score, 1.0)}


def rbi_agent(state: State):
    t = state["transaction"]
    flags = []

    if t["velocity_7d"] > 25:
        flags.append("EWS_VELOCITY_SPIKE")
    if t["amount"] > 100000:
        flags.append("HIGH_VALUE_ALERT")

    return {"rbi_flags": flags}


def fusion_agent(state: State):
    fraud = state.get("fraud_score", 0)
    aml = state.get("aml_score", 0)
    flags = state.get("rbi_flags", [])

    risk = (
        fraud * 0.5 +
        aml * 0.4 +
        len(flags) * 0.1
    )

    return {"risk_score": risk}


def decision_agent(state: State):
    r = state.get("risk_score", 0)

    if r < 0.3:
        decision = "APPROVE"
    elif r < 0.7:
        decision = "REVIEW"
    else:
        decision = "BLOCK"

    return {"decision": decision}

# ---------------- ROUTER (AGENTIC ENTRY POINT) ----------------

def router(state: State):
    t = state["transaction"]

    route = []

    if t["amount"] > 50000 or t["velocity_7d"] > 30 or t["failed_txn_flag"] == 1:
        route.append("fraud")

    if t["amount"] < 3000 or t["merchant_risk"] > 0.6:
        route.append("aml")

    if not route:
        route.append("fraud")

    return {"route": route}

# ---------------- LANGGRAPH ----------------

def build_graph():
    workflow = StateGraph(State)

    workflow.add_node("router", router)
    workflow.add_node("fraud", fraud_agent)
    workflow.add_node("aml", aml_agent)
    workflow.add_node("rbi", rbi_agent)
    workflow.add_node("fusion", fusion_agent)
    workflow.add_node("decision", decision_agent)

    workflow.set_entry_point("router")

    # conditional routing
    workflow.add_conditional_edges(
        "router",
        lambda state: state["route"]
    )

    # FIXED FLOW (no missing rbi_flags issue anymore)
    workflow.add_edge("fraud", "rbi")
    workflow.add_edge("aml", "rbi")
    workflow.add_edge("rbi", "fusion")
    workflow.add_edge("fusion", "decision")
    workflow.add_edge("decision", END)

    return workflow.compile()

# ---------------- RUN SYSTEM ----------------

app = build_graph()
df = generate_data(200)

results = []

for _, row in df.iterrows():
    output = app.invoke({
        "transaction": row.to_dict()
    })

    results.append({
        **row.to_dict(),
        "fraud_score": output.get("fraud_score", 0),
        "aml_score": output.get("aml_score", 0),
        "risk_score": output.get("risk_score", 0),
        "decision": output.get("decision", "UNKNOWN"),
    })

final_df = pd.DataFrame(results)

# ---------------- DASHBOARD ----------------

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Transactions", len(final_df))
col2.metric("Blocked", len(final_df[final_df["decision"] == "BLOCK"]))
col3.metric("Review", len(final_df[final_df["decision"] == "REVIEW"]))
col4.metric("Approved", len(final_df[final_df["decision"] == "APPROVE"]))

st.subheader("📊 Risk Distribution")
st.bar_chart(final_df["risk_score"])

st.subheader("🚨 High Risk Transactions")
st.dataframe(final_df.sort_values("risk_score", ascending=False).head(20))

st.subheader("📌 Decision Breakdown")
st.bar_chart(final_df["decision"].value_counts())

# ---------------- EXPLANATION ----------------
st.subheader("🧠 Agentic System Behavior")

st.info("""
✔ Router decides which agents to activate  
✔ Fraud / AML agents run conditionally  
✔ RBI compliance always executes  
✔ Fusion agent aggregates risk  
✔ Decision engine outputs final action  
""")
