import streamlit as st
import pandas as pd
import numpy as np
import time
import uuid

from langgraph.graph import StateGraph

st.set_page_config(page_title="SOC Engine", layout="wide")
st.title("🏦 Real-Time Financial Crime SOC (LangGraph + Agentic)")

# =========================
# STATE
# =========================
if "log" not in st.session_state:
    st.session_state.log = []

if "stats" not in st.session_state:
    st.session_state.stats = {"BLOCK": 0, "REVIEW": 0, "APPROVE": 0}


# =========================
# DATA
# =========================
def generate_txn(i):
    return {
        "txn_id": f"T{i}",
        "amount": np.random.randint(100, 20000),
        "velocity": np.random.randint(1, 60),
        "failed_txn": np.random.randint(0, 3),
        "risk_signal": np.random.rand()
    }


# =========================
# AGENTS (LANGGRAPH STYLE)
# =========================
def fraud_agent(state):
    amt = state["amount"]
    score = amt / 20000
    return {"fraud_score": score}


def aml_agent(state):
    vel = state["velocity"]
    return {"aml_score": vel / 60}


def fusion_agent(state):
    risk = (
        state["fraud_score"] * 0.5 +
        state["aml_score"] * 0.3 +
        state["risk_signal"] * 0.2
    )
    return {"risk": round(risk, 2)}


def decision_agent(state):
    r = state["risk"]
    if r > 0.7:
        decision = "BLOCK"
    elif r > 0.4:
        decision = "REVIEW"
    else:
        decision = "APPROVE"
    return {"decision": decision}


# =========================
# BUILD GRAPH
# =========================
def build_graph():
    g = StateGraph(dict)

    g.add_node("fraud", fraud_agent)
    g.add_node("aml", aml_agent)
    g.add_node("fusion", fusion_agent)
    g.add_node("decision", decision_agent)

    g.set_entry_point("fraud")
    g.add_edge("fraud", "aml")
    g.add_edge("aml", "fusion")
    g.add_edge("fusion", "decision")

    return g.compile()


app = build_graph()


# =========================
# STREAM CONTROL
# =========================
start = st.button("▶ Start Stream")

placeholder = st.empty()

if start:

    for i in range(50):

        txn = generate_txn(i)

        result = app.invoke(txn)

        record = {**txn, **result}

        st.session_state.log.append(record)

        decision = result["decision"]
        st.session_state.stats[decision] += 1

        with placeholder.container():

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("TOTAL", len(st.session_state.log))

            with col2:
                st.metric("BLOCK", st.session_state.stats["BLOCK"])
                st.metric("REVIEW", st.session_state.stats["REVIEW"])

            with col3:
                st.write("### Live Feed")

                for idx, r in enumerate(st.session_state.log[-10:]):

                    key = f"{r['txn_id']}_{uuid.uuid4()}"

                    if r["decision"] == "BLOCK":
                        st.error(f"BLOCK | {r['txn_id']} | Risk={r['risk']}")
                    elif r["decision"] == "REVIEW":
                        st.warning(f"REVIEW | {r['txn_id']} | Risk={r['risk']}")
                    else:
                        st.success(f"APPROVE | {r['txn_id']} | Risk={r['risk']}")

                    st.button("Take Action", key=key)

        time.sleep(0.2)

    st.success("Stream Completed")
