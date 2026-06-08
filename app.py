import streamlit as st
import pandas as pd
import numpy as np
import time

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="SOC Fraud Engine", layout="wide")

st.title("🏦 Real-Time Financial Crime SOC (ML + Agentic + HITL)")

# =========================
# SESSION STATE INIT
# =========================
if "log" not in st.session_state:
    st.session_state.log = []

if "stats" not in st.session_state:
    st.session_state.stats = {"BLOCKED": 0, "REVIEW": 0, "APPROVE": 0}

# =========================
# SIMPLE SYNTHETIC STREAM
# =========================
def generate_txn(i):
    return {
        "txn_id": f"T{i}",
        "amount": np.random.randint(100, 20000),
        "velocity": np.random.randint(1, 50),
        "failed_txn": np.random.randint(0, 3),
        "risk_signal": np.random.rand()
    }

# =========================
# SIMPLE ML-LIKE RISK ENGINE
# =========================
def risk_engine(txn):
    score = (
        txn["amount"] / 20000 * 0.4 +
        txn["velocity"] / 50 * 0.3 +
        txn["failed_txn"] * 0.2 +
        txn["risk_signal"] * 0.1
    )
    return float(min(score, 1.0))

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
# STREAM CONTROL
# =========================
start = st.button("▶ Start Live Stream")

stop = st.button("⛔ Stop Stream")

placeholder = st.empty()

# =========================
# STREAM LOOP (SIMULATED)
# =========================
if start:
    for i in range(50):

        txn = generate_txn(i)
        risk = risk_engine(txn)
        decision = decision_agent(risk)

        record = {
            **txn,
            "risk": risk,
            "decision": decision
        }

        st.session_state.log.append(record)

        st.session_state.stats[decision] += 1

        with placeholder.container():

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("TOTAL", len(st.session_state.log))
                st.metric("BLOCKED", st.session_state.stats["BLOCKED"])

            with col2:
                st.metric("REVIEW", st.session_state.stats["REVIEW"])
                st.metric("APPROVE", st.session_state.stats["APPROVE"])

            with col3:
                st.write("### 🚨 Live Feed")

                for r in st.session_state.log[-10:]:
                    if r["decision"] == "BLOCK":
                        st.error(f"BLOCK | {r['txn_id']} | Risk={r['risk']:.2f}")
                    elif r["decision"] == "REVIEW":
                        st.warning(f"REVIEW | {r['txn_id']} | Risk={r['risk']:.2f}")
                    else:
                        st.success(f"APPROVE | {r['txn_id']} | Risk={r['risk']:.2f}")

        time.sleep(0.2)

    st.success("Stream Completed (Prototype Mode)")
