import streamlit as st
import pandas as pd
import random
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

# ---------------- STREAMLIT CONFIG ----------------
st.set_page_config(page_title="Financial Crime SOC", layout="wide")
st.title("🏦 Real-Time Financial Crime Intelligence Platform")

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
    return {
        "risk_score": (
            state["fraud_score"] * 0.5 +
            state["aml_score"] * 0.4 +
            len(state["rbi_flags"]) * 0.1
        )
    }


def decision_agent(state: State):
    r = state["risk_score"]

    if r < 0.3:
        decision = "APPROVE"
    elif r < 0.7:
        decision = "REVIEW"
    else:
        decision = "BLOCK"

    return {"decision": decision}

# ---------------- LANGGRAPH ----------------

def build_graph():
    workflow = StateGraph(State)

    workflow.add_node("fraud", fraud_agent)
    workflow.add_node("aml", aml_agent)
    workflow.add_node("rbi", rbi_agent)
    workflow.add_node("fusion", fusion_agent)
    workflow.add_node("decision", decision_agent)

    workflow.set_entry_point("fraud")

    workflow.add_edge("fraud", "aml")
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
        "fraud_score": output["fraud_score"],
        "aml_score": output["aml_score"],
        "risk_score": output["risk_score"],
        "decision": output["decision"]
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
