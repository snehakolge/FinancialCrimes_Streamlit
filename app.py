import streamlit as st
import pandas as pd
import numpy as np
import time

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="SOC Fraud Engine", layout="wide")

st.title("🏦 Real-Time Financial Crime SOC (Agentic + HITL)")

# =========================
# SESSION STATE INIT
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
# BUTTON CONTROL
# =========================
colA, colB = st.columns(2)

with colA:
    if st.button("▶ Start Live Stream"):
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
# RISK ENGINE (SIMPLE ML SIMULATION)
# =========================
def risk_engine(txn):
    score = (
        txn["amount"] / 20000 * 0.4 +
        txn["velocity"] / 60 * 0.3 +
        txn["failed_txn"] * 0.2 +
        txn["risk_signal"] * 0.1
    )
    return round(min(score, 1.0), 2)


# =========================
# AGENT DECISION ENGINE
# =========================
def decision_agent(risk):
    if risk > 0.70:
        return "BLOCK"
    elif risk > 0.40:
        return "REVIEW"
    else:
        return "APPROVE"


# =========================
# LIVE STREAM PLACEHOLDER
# =========================
placeholder = st.empty()


# =========================
# STREAM LOOP (SAFE CONTROLLED)
# =========================
if st.session_state.running:

    for i in range(50):

        # STOP CONDITION
        if not st.session_state.running:
            break

        txn = generate_txn(i)
        risk = risk_engine(txn)
        decision = decision_agent(risk)

        record = {
            **txn,
            "risk": risk,
            "decision": decision
        }

        st.session_state.log.append(record)

        # =========================
        # SAFE STAT UPDATE (FIXED KEYERROR)
        # =========================
        if decision not in st.session_state.stats:
            st.session_state.stats[decision] = 0

        st.session_state.stats[decision] += 1

        # =========================
        # LIVE DASHBOARD
        # =========================
        with placeholder.container():

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("TOTAL TRANSACTIONS", len(st.session_state.log))
                st.metric("BLOCKED", st.session_state.stats.get("BLOCK", 0))

            with col2:
                st.metric("REVIEW", st.session_state.stats.get("REVIEW", 0))
                st.metric("APPROVE", st.session_state.stats.get("APPROVE", 0))

            with col3:
                st.write("### 🚨 Live Agentic Feed")

                for idx, r in enumerate(st.session_state.log[-10:]):

                    key = f"btn_{r['txn_id']}_{idx}"

                    if r["decision"] == "BLOCK":
                        st.error(f"BLOCK | {r['txn_id']} | Risk={r['risk']}")
                    elif r["decision"] == "REVIEW":
                        st.warning(f"REVIEW | {r['txn_id']} | Risk={r['risk']}")
                    else:
                        st.success(f"APPROVE | {r['txn_id']} | Risk={r['risk']}")

                    # OPTIONAL ACTION BUTTON (FIXED UNIQUE KEY)
                    st.button(
                        f"Take Action {r['txn_id']}",
                        key=key
                    )

        time.sleep(0.2)

    st.success("Stream Completed (Stable Prototype Mode)")
    st.session_state.running = False
