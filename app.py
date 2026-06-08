import streamlit as st
import pandas as pd
import numpy as np
import time

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="SOC", layout="wide")
st.title("Real-Time Financial Crime SOC (Agentic + HITL)")

# ---------------------------
# STATE
# ---------------------------
if "override_log" not in st.session_state:
    st.session_state.override_log = {}

# ---------------------------
# DATA GENERATION
# ---------------------------
def generate_data(n=50):
    np.random.seed(7)
    return pd.DataFrame({
        "transaction_id": [f"T{i}" for i in range(n)],
        "amount": np.random.randint(100, 20000, n),
        "velocity": np.random.randint(1, 60, n),
        "failed_txn": np.random.randint(0, 2, n),
    })

df = generate_data(50)

# ---------------------------
# AGENTS
# ---------------------------

def fraud_agent(txn):
    score = (
        txn["amount"] / 20000 * 0.5 +
        txn["velocity"] / 60 * 0.3 +
        txn["failed_txn"] * 0.2
    )
    return min(1.0, score)


def aml_agent(txn):
    return min(1.0, txn["velocity"] / 60)


def rbi_agent(txn):
    flags = []
    if txn["amount"] > 15000:
        flags.append("HIGH_VALUE")
    if txn["velocity"] > 40:
        flags.append("VELOCITY_SPIKE")
    return flags


def fusion_agent(fraud, aml, rbi_flags):
    return min(1.0, fraud * 0.5 + aml * 0.3 + len(rbi_flags) * 0.2)


def decision_agent(score):
    if score >= 0.7:
        return "BLOCK"
    elif score >= 0.4:
        return "REVIEW"
    return "APPROVE"


def alert_engine(txn_id, decision, score):
    if decision == "BLOCK":
        return f"🚨 BLOCK ALERT | {txn_id} | Risk={score:.2f}"
    elif decision == "REVIEW":
        return f"⚠️ REVIEW ALERT | {txn_id} | Risk={score:.2f}"
    return f"🟢 APPROVED | {txn_id} | Risk={score:.2f}"


# ---------------------------
# UI PLACEHOLDERS
# ---------------------------
col1, col2, col3 = st.columns(3)
t_box = col1.empty()
b_box = col2.empty()
r_box = col3.empty()

feed = st.empty()
override = st.empty()

# ---------------------------
# STREAM
# ---------------------------
results = []

for _, row in df.iterrows():

    fraud = fraud_agent(row)
    aml = aml_agent(row)
    rbi_flags = rbi_agent(row)
    score = fusion_agent(fraud, aml, rbi_flags)
    decision = decision_agent(score)

    alert = alert_engine(row["transaction_id"], decision, score)

    results.append({
        "txn": row["transaction_id"],
        "score": score,
        "decision": decision
    })

    temp = pd.DataFrame(results)

    # counters
    total = len(temp)
    blocked = len(temp[temp["decision"] == "BLOCK"])
    review = len(temp[temp["decision"] == "REVIEW"])

    t_box.metric("TOTAL", total)
    b_box.metric("BLOCKED", blocked)
    r_box.metric("REVIEW", review)

    # LIVE FEED (auto alerts)
    feed.markdown("## 📡 Live Agent Alert Stream")

    for r in results[-12:]:
        icon = "🔴" if r["decision"] == "BLOCK" else "🟡" if r["decision"] == "REVIEW" else "🟢"
        feed.write(f"{icon} {r['txn']} | {r['decision']} | Risk={r['score']:.2f}")

    # AUTO ALERT PUSH (IMPORTANT PART)
    st.toast(alert)

    # override log view
    override.markdown("## 🧠 Human Override Log")
    override.json(st.session_state.override_log)

    time.sleep(0.25)

st.success("Live Agentic Stream Completed")
