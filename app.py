import streamlit as st
import pandas as pd
import numpy as np
import time
import random

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(page_title="Financial Crime SOC", layout="wide")

st.title("🏦 Real-Time Financial Crime SOC (Agentic + HITL)")

# ==============================
# SESSION STATE INIT
# ==============================
if "transactions" not in st.session_state:
    st.session_state.transactions = []

if "override_log" not in st.session_state:
    st.session_state.override_log = {}

if "counter" not in st.session_state:
    st.session_state.counter = 0


# ==============================
# SYNTHETIC TRANSACTION STREAM
# ==============================
def generate_transaction(i):
    amount = random.randint(100, 20000)
    velocity = random.randint(1, 50)

    fraud_score = min(1, np.random.rand() + (amount / 20000))
    aml_score = min(1, np.random.rand() + (velocity / 50))

    return {
        "transaction_id": f"T{i}",
        "amount": amount,
        "velocity": velocity,
        "fraud_score": fraud_score,
        "aml_score": aml_score
    }


# ==============================
# AGENTS
# ==============================
def fraud_agent(txn):
    return txn["fraud_score"]


def aml_agent(txn):
    return txn["aml_score"]


def fusion_agent(txn):
    # SAFE fusion (NO missing keys anymore)
    risk = (
        txn["fraud_score"] * 0.6 +
        txn["aml_score"] * 0.4
    )
    return risk


def decision_agent(risk):
    if risk > 0.65:
        return "BLOCK"
    elif risk > 0.35:
        return "REVIEW"
    else:
        return "APPROVE"


# ==============================
# PROCESS ONE TRANSACTION
# ==============================
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


# ==============================
# LIVE STREAM CONTROLS
# ==============================
col1, col2 = st.columns(2)

start = col1.button("▶ Start Live Stream")
stop = col2.button("⛔ Stop")

placeholder = st.empty()


# ==============================
# STREAM LOOP (SAFE)
# ==============================
if start:
    for i in range(st.session_state.counter, st.session_state.counter + 50):

        if stop:
            break

        txn = generate_transaction(i)
        txn = process_transaction(txn)

        st.session_state.transactions.append(txn)
        st.session_state.counter += 1

        df = pd.DataFrame(st.session_state.transactions)

        # ==========================
        # DASHBOARD METRICS
        # ==========================
        colA, colB, colC = st.columns(3)

        colA.metric("TOTAL", len(df))
        colB.metric("BLOCKED", len(df[df["decision"] == "BLOCK"]))
        colC.metric("REVIEW", len(df[df["decision"] == "REVIEW"]))

        # ==========================
        # LIVE TABLE
        # ==========================
        with placeholder.container():

            st.subheader("🚨 Live Transactions Stream")

            st.dataframe(df.tail(20), use_container_width=True)

            st.subheader("🧠 Agentic Alerts")

            for idx, row in df.tail(10).iterrows():

                txn_id = row["transaction_id"]

                if row["decision"] == "BLOCK":
                    st.error(f"BLOCKED | {txn_id} | Risk={row['risk_score']}")

                elif row["decision"] == "REVIEW":
                    st.warning(f"REVIEW REQUIRED | {txn_id} | Risk={row['risk_score']}")

                    # ==========================
                    # HITL OVERRIDE (FIXED KEYS)
                    # ==========================
                    key1 = f"approve_{txn_id}_{idx}"
                    key2 = f"block_{txn_id}_{idx}"

                    colA, colB = st.columns(2)

                    with colA:
                        if st.button("Approve", key=key1):
                            st.session_state.override_log[txn_id] = "APPROVED"

                    with colB:
                        if st.button("Block", key=key2):
                            st.session_state.override_log[txn_id] = "BLOCKED"

                else:
                    st.success(f"APPROVED | {txn_id}")

            st.subheader("📌 Override Log")
            st.json(st.session_state.override_log)

        time.sleep(0.4)

st.info("Click START to begin real-time agentic transaction stream.")
