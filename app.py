import streamlit as st
import pandas as pd
import numpy as np
import time
import random

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Financial Crime SOC", layout="wide")

st.title("🏦 Real-Time Financial Crime SOC (Agentic + HITL)")

# =========================
# SESSION STATE INIT
# =========================
if "transactions" not in st.session_state:
    st.session_state.transactions = []

if "counter" not in st.session_state:
    st.session_state.counter = 0

if "run_stream" not in st.session_state:
    st.session_state.run_stream = False

if "override_log" not in st.session_state:
    st.session_state.override_log = {}


# =========================
# SYNTHETIC TRANSACTION GENERATOR
# =========================
def generate_transaction(i):
    amount = random.randint(100, 20000)
    velocity = random.randint(1, 50)

    fraud_score = min(1, np.random.rand() + amount / 20000)
    aml_score = min(1, np.random.rand() + velocity / 50)

    return {
        "transaction_id": f"T{i}",
        "amount": amount,
        "velocity": velocity,
        "fraud_score": fraud_score,
        "aml_score": aml_score
    }


# =========================
# AGENTS
# =========================
def fraud_agent(txn):
    return txn["fraud_score"]

def aml_agent(txn):
    return txn["aml_score"]

def fusion_agent(txn):
    return txn["fraud_score"] * 0.6 + txn["aml_score"] * 0.4

def decision_agent(risk):
    if risk > 0.65:
        return "BLOCK"
    elif risk > 0.35:
        return "REVIEW"
    return "APPROVE"


# =========================
# PROCESS TRANSACTION
# =========================
def process_transaction(txn):
    fraud = fraud_agent(txn)
    aml = aml_agent(txn)
    risk = fusion_agent(txn)
    decision = decision_agent(risk)

    txn.update({
        "fraud_score": round(fraud, 2),
        "aml_score": round(aml, 2),
        "risk_score": round(risk, 2),
        "decision": decision
    })

    return txn


# =========================
# CONTROLS
# =========================
col1, col2 = st.columns(2)

if col1.button("▶ START LIVE STREAM"):
    st.session_state.run_stream = True

if col2.button("⛔ STOP STREAM"):
    st.session_state.run_stream = False


# =========================
# STREAM GENERATION (SAFE)
# =========================
if st.session_state.run_stream:

    txn = generate_transaction(st.session_state.counter)
    txn = process_transaction(txn)

    st.session_state.transactions.append(txn)
    st.session_state.counter += 1

    time.sleep(0.4)

    st.rerun()


# =========================
# DASHBOARD RENDER
# =========================
df = pd.DataFrame(st.session_state.transactions)

if len(df) > 0:

    # KPIs
    colA, colB, colC = st.columns(3)

    colA.metric("TOTAL TRANSACTIONS", len(df))
    colB.metric("BLOCKED", len(df[df["decision"] == "BLOCK"]))
    colC.metric("REVIEW", len(df[df["decision"] == "REVIEW"]))

    st.divider()

    # LIVE TABLE
    st.subheader("📡 Live Transaction Feed")

    st.dataframe(df.tail(30), use_container_width=True)

    st.divider()

    # ALERT PANEL
    st.subheader("🚨 Agentic Alerts")

    for i, row in df.tail(10).iterrows():

        tx_id = row["transaction_id"]

        if row["decision"] == "BLOCK":
            st.error(f"BLOCKED | {tx_id} | Risk={row['risk_score']}")

        elif row["decision"] == "REVIEW":
            st.warning(f"REVIEW REQUIRED | {tx_id} | Risk={row['risk_score']}")

            # =========================
            # HITL OVERRIDE (FIXED KEYS)
            # =========================
            key_approve = f"approve_{tx_id}_{i}"
            key_block = f"block_{tx_id}_{i}"

            col1, col2 = st.columns(2)

            with col1:
                if st.button("✔ Approve", key=key_approve):
                    st.session_state.override_log[tx_id] = "APPROVED"

            with col2:
                if st.button("⛔ Block", key=key_block):
                    st.session_state.override_log[tx_id] = "BLOCKED"

        else:
            st.success(f"APPROVED | {tx_id}")

    st.divider()

    # OVERRIDE LOG
    st.subheader("📌 Human Override Log")
    st.json(st.session_state.override_log)

else:
    st.info("Click START to begin real-time transaction streaming.")
