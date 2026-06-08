import streamlit as st
import pandas as pd
import random
import time
from typing import TypedDict, Dict, Any, List

from langgraph.graph import StateGraph, END


# =====================================================
# STATE
# =====================================================
class TxnState(TypedDict):
    transaction: Dict[str, Any]
    fraud_score: float
    aml_score: float
    rbi_flags: List[str]
    risk_score: float
    decision: str


# =====================================================
# AGENTS
# =====================================================
def fraud_agent(state):
    tx = state["transaction"]
    score = tx.get("amount", 0)/10000 + tx.get("velocity_7d", 0)/50
    return {"fraud_score": min(score, 1.0)}


def aml_agent(state):
    tx = state["transaction"]
    score = tx.get("amount", 0)/20000 + tx.get("customer_risk", 0.3)
    return {"aml_score": min(score, 1.0)}


def rbi_agent(state):
    tx = state["transaction"]
    flags = []

    if tx.get("amount", 0) > 10000:
        flags.append("HIGH_VALUE")

    if tx.get("is_night", 0):
        flags.append("NIGHT_TXN")

    if tx.get("velocity_7d", 0) > 20:
        flags.append("VELOCITY_SPIKE")

    return {"rbi_flags": flags}


def fusion_agent(state):
    fraud = state.get("fraud_score", 0)
    aml = state.get("aml_score", 0)
    flags = state.get("rbi_flags", [])

    risk = fraud * 0.5 + aml * 0.4 + len(flags) * 0.1
    risk = min(risk, 1.0)

    if risk >= 0.7:
        decision = "BLOCK"
    elif risk >= 0.4:
        decision = "REVIEW"
    else:
        decision = "APPROVE"

    return {"risk_score": risk, "decision": decision}


# =====================================================
# GRAPH BUILDER (IN SAME FILE)
# =====================================================
def build_graph():
    g = StateGraph(TxnState)

    g.add_node("fraud", fraud_agent)
    g.add_node("aml", aml_agent)
    g.add_node("rbi", rbi_agent)
    g.add_node("fusion", fusion_agent)

    g.set_entry_point("fraud")

    g.add_edge("fraud", "aml")
    g.add_edge("aml", "rbi")
    g.add_edge("rbi", "fusion")

    g.add_conditional_edges(
        "fusion",
        lambda s: s["decision"],
        {
            "BLOCK": END,
            "REVIEW": END,
            "APPROVE": END
        }
    )

    return g.compile()


# =====================================================
# SYNTHETIC DATA
# =====================================================
def generate_data(n=50):
    return [
        {
            "transaction_id": f"T{i}",
            "amount": random.randint(100, 20000),
            "velocity_7d": random.randint(1, 60),
            "failed_txn_flag": random.randint(0, 1),
            "is_night": random.randint(0, 1),
            "customer_risk": round(random.random(), 2)
        }
        for i in range(n)
    ]


# =====================================================
# STREAMLIT APP
# =====================================================
st.set_page_config(page_title="SOC Platform", layout="wide")

st.title("🏦 Real-Time Financial Crime SOC (Single File Version)")


# INIT
if "actions" not in st.session_state:
    st.session_state.actions = {}

app = build_graph()
df = pd.DataFrame(generate_data(50))

results = []

for row in df.to_dict(orient="records"):

    output = app.invoke({
        "transaction": row,
        "fraud_score": 0,
        "aml_score": 0,
        "rbi_flags": [],
        "risk_score": 0,
        "decision": ""
    })

    results.append({**row, **output})

result_df = pd.DataFrame(results)


# DASHBOARD
c1, c2, c3 = st.columns(3)
c1.metric("TOTAL", len(result_df))
c2.metric("BLOCKED", len(result_df[result_df["decision"] == "BLOCK"]))
c3.metric("REVIEW", len(result_df[result_df["decision"] == "REVIEW"]))

st.divider()
st.subheader("Live Stream")

# LIVE TABLE
for i, row in result_df.iterrows():

    with st.container(border=True):

        st.write(row["transaction_id"], row["amount"], row["decision"])

        tx = row["transaction_id"]

        k1 = f"ap_{tx}_{i}"
        k2 = f"bl_{tx}_{i}"

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Approve", key=k1):
                st.session_state.actions[tx] = "APPROVED"

        with col2:
            if st.button("Block", key=k2):
                st.session_state.actions[tx] = "BLOCKED"

        time.sleep(0.03)


st.divider()
st.subheader("Override Log")
st.write(st.session_state.actions)
