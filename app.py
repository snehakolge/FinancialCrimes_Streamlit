import streamlit as st
import pandas as pd
import numpy as np
import random
import time

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Financial Crime SOC", layout="wide")

st.title("🏦 Real-Time Financial Crime SOC (Agentic + HITL)")

# =========================
# SESSION STATE
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
# REALISTIC TRANSACTION GENERATOR
# =========================
def generate_transaction(i):
    amount = random.randint(100, 20000)
    velocity = random.randint(1, 50)

    # Normalized signals
    amount_score = amount / 20000
    velocity_score = velocity / 50

    # REALISTIC DISTRIBUTION (IMPORTANT FIX)
    fraud_score = np.clip(
        np.random.normal(0.3 + amount_score * 0.4, 0.12),
        0, 1
    )

    aml_score = np.clip(
        np.random.normal(0.25 + velocity_score * 0.35, 0.12),
        0, 1
    )

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
    if risk > 0.70:
        return "BLOCK"
    elif risk > 0.40:
        return "REVIEW"
    else:
        return "APPROVE"


# =========================
# PROCESSOR
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

if col1.button("▶ START STREAM"):
    st.session_state.run_stream = True

if col2.button("⛔ STOP STREAM"):
    st.session_state.run_stream = False


# =========================
# STREAM ENGINE (SAFE)
# =========================
if st.session_state.run_stream:

    txn = generate_transaction(st.session_state.counter)
    txn = process_transaction(txn)

    st.session_state.transactions.append(txn)
    st.session_state.counter += 1

    time.sleep(0.35)
    st.rerun()


# =========================
# DASHBOARD
# =========================
df = pd.DataFrame(st.session_state.transactions)

if len(df) > 0:

    # KPIs
    colA, colB, colC = st.columns(3)

    colA.metric("TOTAL TRANSACTIONS", len(df))
    colB.metric("BLOCKED", len(df[df["decision"] == "BLOCK"]))
    colC.metric("REVIEW", len(df[df["decision"] == "REVIEW"]))

    st.divider()

    # LIVE FEED
    st.subheader("📡 Live Transaction Feed")
    st.dataframe(df.tail(25), use_container_width=True)

    st.divider()

    # ALERT ENGINE
    st.subheader("🚨 Agentic Alerts")

    for i, row in df.tail(10).iterrows():

        tx_id = row["transaction_id"]

        if row["decision"] == "BLOCK":
            st.error(f"BLOCKED | {tx_id} | Risk={row['risk_score']}")

        elif row["decision"] == "REVIEW":
            st.warning(f"REVIEW REQUIRED | {tx_id} | Risk={row['risk_score']}")

            # UNIQUE KEYS (CRITICAL FIX)
            key_a = f"approve_{tx_id}_{i}"
            key_b = f"block_{tx_id}_{i}"

            c1, c2 = st.columns(2)

            with c1:
                if st.button("✔ Approve", key=key_a):
                    st.session_state.override_log[tx_id] = "APPROVED"

            with c2:
                if st.button("⛔ Block", key=key_b):
                    st.session_state.override_log[tx_id] = "BLOCKED"

        else:
            st.success(f"APPROVED | {tx_id}")

    st.divider()

    # OVERRIDE LOG
    st.subheader("📌 Human Override Log")
    st.json(st.session_state.override_log)

else:
    st.info("Click START to begin real-time SOC simulation.")
