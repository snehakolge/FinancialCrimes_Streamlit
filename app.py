import streamlit as st
import numpy as np
import time
import uuid

from langgraph.graph import StateGraph

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="SOC Engine", layout="wide")
st.title("🏦 Real-Time Financial Crime SOC (Agentic + LangGraph + HITL)")


# =========================
# SESSION STATE
# =========================
if "log" not in st.session_state:
    st.session_state.log = []

if "stats" not in st.session_state:
    st.session_state.stats = {
        "BLOCK": 0,
        "REVIEW": 0,
        "APPROVE": 0
    }

if "running" not in st.session_state:
    st.session_state.running = False


# =========================
# CONTROL BUTTONS
# =========================
colA, colB = st.columns(2)

with colA:
    if st.button("▶ Start Stream"):
        st.session_state.running = True

with colB:
    if st.button("⛔ Stop Stream"):
        st.session_state.running = False


# =========================
# TRANSACTION GENERATOR
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
# LANGGRAPH AGENTS (SAFE STATE PASSING)
# =========================
def fraud_agent(state):
    state["fraud_score"] = state.get("amount", 0) / 20000
    return state


def aml_agent(state):
    state["aml_score"] = state.get("velocity", 0) / 60
    return state


def fusion_agent(state):
    state["risk"] = (
        state.get("fraud_score", 0) * 0.5 +
        state.get("aml_score", 0) * 0.3 +
        state.get("risk_signal", 0) * 0.2
    )
    return state


def decision_agent(state):
    r = state.get("risk", 0)

    if r > 0.70:
        state["decision"] = "BLOCK"
    elif r > 0.40:
        state["decision"] = "REVIEW"
    else:
        state["decision"] = "APPROVE"

    return state


# =========================
# BUILD LANGGRAPH PIPELINE
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
# UI PLACEHOLDER
# =========================
placeholder = st.empty()


# =========================
# LIVE STREAM LOOP
# =========================
if st.session_state.running:

    for i in range(50):

        if not st.session_state.running:
            break

        txn = generate_txn(i)

        # LangGraph execution
        result = app.invoke(txn.copy())

        st.session_state.log.append(result)

        decision = result.get("decision", "REVIEW")

        if decision not in st.session_state.stats:
            st.session_state.stats[decision] = 0

        st.session_state.stats[decision] += 1

        # =========================
        # DASHBOARD UI
        # =========================
        with placeholder.container():

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("TOTAL", len(st.session_state.log))

            with col2:
                st.metric("BLOCK", st.session_state.stats.get("BLOCK", 0))
                st.metric("REVIEW", st.session_state.stats.get("REVIEW", 0))

            with col3:
                st.write("### 🚨 Live Feed")

                for idx, r in enumerate(st.session_state.log[-10:]):

                    # 🔥 FIXED UNIQUE KEY (NO DUPLICATE ERROR EVER)
                    key = f"{r['txn_id']}_{uuid.uuid4()}"

                    if r["decision"] == "BLOCK":
                        st.error(f"BLOCK | {r['txn_id']} | Risk={r.get('risk', 0):.2f}")
                    elif r["decision"] == "REVIEW":
                        st.warning(f"REVIEW | {r['txn_id']} | Risk={r.get('risk', 0):.2f}")
                    else:
                        st.success(f"APPROVE | {r['txn_id']} | Risk={r.get('risk', 0):.2f}")

                    st.button("Take Action", key=key)

        time.sleep(0.2)

    st.session_state.running = False
    st.success("Stream Completed (Stable LangGraph SOC)")
