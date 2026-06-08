import streamlit as st
import pandas as pd
import random
import plotly.express as px

from typing import TypedDict, List
from langgraph.graph import StateGraph, END

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="Financial Crime SOC", layout="wide")

st.title("🏦 Real-Time Financial Crime SOC (Agentic + HITL)")


# =============================
# SYNTHETIC DATA GENERATION
# =============================
def generate_data(n=50):
    data = []
    for i in range(n):
        data.append({
            "transaction_id": f"T{i}",
            "amount": random.randint(500, 120000),
            "velocity_7d": random.randint(1, 50),
            "failed_txn_flag": random.randint(0, 1),
            "merchant_risk": round(random.random(), 2)
        })
    return pd.DataFrame(data)


# =============================
# AGENT STATE
# =============================
class State(TypedDict, total=False):
    transaction: dict
    fraud_score: float
    aml_score: float
    rbi_flags: List[str]
    risk_score: float
    decision: str


# =============================
# AGENTS (SAFE + ROBUST)
# =============================
def fraud_agent(state: State):
    t = state["transaction"]
    score = 0.0

    if t.get("amount", 0) > 50000:
        score += 0.4
    if t.get("velocity_7d", 0) > 30:
        score += 0.3
    if t.get("failed_txn_flag", 0) == 1:
        score += 0.2

    return {"fraud_score": min(score, 1.0)}


def aml_agent(state: State):
    t = state["transaction"]
    score = 0.0

    if t.get("amount", 0) < 3000:
        score += 0.5
    if t.get("merchant_risk", 0) > 0.6:
        score += 0.3

    return {"aml_score": min(score, 1.0)}


def rbi_agent(state: State):
    t = state["transaction"]
    flags = []

    if t.get("velocity_7d", 0) > 25:
        flags.append("EWS_VELOCITY_SPIKE")
    if t.get("amount", 0) > 100000:
        flags.append("HIGH_VALUE_ALERT")

    return {"rbi_flags": flags}


def fusion_agent(state: State):
    fraud = state.get("fraud_score", 0)
    aml = state.get("aml_score", 0)
    flags = state.get("rbi_flags", [])

    risk = fraud * 0.5 + aml * 0.4 + len(flags) * 0.1
    return {"risk_score": risk}


def decision_agent(state: State):
    r = state.get("risk_score", 0)

    if r < 0.3:
        d = "APPROVE"
    elif r < 0.7:
        d = "REVIEW"
    else:
        d = "BLOCK"

    return {"decision": d}


# =============================
# BUILD GRAPH (FIXED)
# =============================
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


app = build_graph()


# =============================
# SESSION STATE (HITL MEMORY)
# =============================
if "actions" not in st.session_state:
    st.session_state.actions = {}


# =============================
# LOAD STREAM DATA
# =============================
df = generate_data(50)

results = []

# =============================
# AGENTIC STREAM PROCESSING
# =============================
for _, row in df.iterrows():

    output = app.invoke({
        "transaction": row.to_dict(),
        "rbi_flags": []   # IMPORTANT default safety
    })

    row_dict = row.to_dict()
    row_dict.update(output)

    results.append(row_dict)

result_df = pd.DataFrame(results)


# =============================
# KPIs
# =============================
col1, col2, col3 = st.columns(3)

col1.metric("Total Transactions", len(result_df))
col2.metric("BLOCKED", len(result_df[result_df["decision"] == "BLOCK"]))
col3.metric("REVIEW", len(result_df[result_df["decision"] == "REVIEW"]))


# =============================
# RISK DISTRIBUTION
# =============================
fig = px.histogram(result_df, x="risk_score", nbins=20, title="📊 Risk Distribution")
st.plotly_chart(fig, use_container_width=True)


# =============================
# LIVE ALERT STREAM (AUTO)
# =============================
st.subheader("🚨 Agentic Alerts (Auto Generated)")

for i, row in result_df.iterrows():

    if row["decision"] == "BLOCK":
        st.error(
            f"🚨 AUTO BLOCK | {row['transaction_id']} | Risk={row['risk_score']:.2f}"
        )

        key1 = f"approve_{row['transaction_id']}_{i}"
        key2 = f"reject_{row['transaction_id']}_{i}"

        colA, colB = st.columns(2)

        with colA:
            if st.button("👤 Override → Approve", key=key1):
                st.session_state.actions[row["transaction_id"]] = "APPROVED_BY_HUMAN"

        with colB:
            if st.button("❌ Confirm Block", key=key2):
                st.session_state.actions[row["transaction_id"]] = "BLOCK_CONFIRMED"


    elif row["decision"] == "REVIEW":
        st.warning(
            f"⚠️ REVIEW REQUIRED | {row['transaction_id']} | Risk={row['risk_score']:.2f}"
        )

        key3 = f"review_{row['transaction_id']}_{i}"

        if st.button("👤 Approve After Review", key=key3):
            st.session_state.actions[row["transaction_id"]] = "REVIEW_APPROVED"


    else:
        st.success(f"✔ APPROVED | {row['transaction_id']}")


# =============================
# HUMAN OVERRIDE TABLE
# =============================
st.subheader("🧠 Human Override Log")

if st.session_state.actions:
    st.dataframe(pd.DataFrame([
        {"transaction_id": k, "action": v}
        for k, v in st.session_state.actions.items()
    ]))
else:
    st.info("No human overrides yet.")


# =============================
# FINAL INSIGHT
# =============================
st.subheader("📌 Decision Breakdown")

st.bar_chart(result_df["decision"].value_counts())
