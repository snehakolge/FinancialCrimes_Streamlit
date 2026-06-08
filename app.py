import streamlit as st
import pandas as pd
import random
import time

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(page_title="Financial Crime SOC", layout="wide")

st.title("🏦 Real-Time Financial Crime SOC (Agentic + HITL)")

# ==============================
# SESSION STATE INIT
# ==============================
if "i" not in st.session_state:
    st.session_state.i = 0

if "logs" not in st.session_state:
    st.session_state.logs = []

if "data" not in st.session_state:
    st.session_state.data = []

if "human_actions" not in st.session_state:
    st.session_state.human_actions = []


# ==============================
# SYNTHETIC LIVE TRANSACTIONS
# ==============================
def generate_txn(i):
    return {
        "transaction_id": f"T{i}",
        "amount": random.randint(500, 120000),
        "velocity_7d": random.randint(1, 60),
        "failed_txn_flag": random.randint(0, 1),
        "merchant_risk": round(random.random(), 2),
    }


# ==============================
# AGENTS
# ==============================
def fraud_agent(t):
    score = 0
    if t["amount"] > 50000:
        score += 0.4
    if t["velocity_7d"] > 30:
        score += 0.3
    if t["failed_txn_flag"] == 1:
        score += 0.2
    return min(score, 1.0)


def aml_agent(t):
    score = 0
    if t["amount"] < 3000:
        score += 0.4
    if t["merchant_risk"] > 0.6:
        score += 0.4
    return min(score, 1.0)


def rbi_agent(t):
    flags = []
    if t["velocity_7d"] > 25:
        flags.append("EWS_VELOCITY_SPIKE")
    if t["amount"] > 100000:
        flags.append("HIGH_VALUE_ALERT")
    return flags


def fusion_agent(fraud, aml, flags):
    return fraud * 0.5 + aml * 0.4 + len(flags) * 0.1


def decision_agent(risk):
    if risk < 0.3:
        return "APPROVE"
    elif risk < 0.7:
        return "REVIEW"
    else:
        return "BLOCK"


# ==============================
# PROCESS PIPELINE (AGENTIC FLOW)
# ==============================
def process(txn):
    fraud = fraud_agent(txn)
    aml = aml_agent(txn)
    flags = rbi_agent(txn)

    risk = fusion_agent(fraud, aml, flags)
    decision = decision_agent(risk)

    return {
        **txn,
        "fraud_score": fraud,
        "aml_score": aml,
        "rbi_flags": flags,
        "risk_score": risk,
        "decision": decision,
    }


# ==============================
# HUMAN OVERRIDE
# ==============================
def human_override(txn_id, new_decision):
    st.session_state.human_actions.append({
        "txn": txn_id,
        "override": new_decision
    })


# ==============================
# UI CONTROL PANEL
# ==============================
col1, col2, col3 = st.columns(3)

start = col1.button("▶ Start Live Stream")
stop = col2.button("⛔ Stop")
reset = col3.button("🔄 Reset System")

if reset:
    st.session_state.i = 0
    st.session_state.logs = []
    st.session_state.data = []
    st.session_state.human_actions = []

# ==============================
# STREAM CONTROL
# ==============================
placeholder = st.empty()

running = start and not stop

if running:

    for _ in range(200):  # simulate stream limit

        i = st.session_state.i
        txn = generate_txn(i)

        result = process(txn)

        st.session_state.data.append(result)

        # ALERT LOGGING
        if result["decision"] == "BLOCK":
            st.session_state.logs.append(f"🚨 BLOCK {result['transaction_id']} | Risk={result['risk_score']:.2f}")

        elif result["decision"] == "REVIEW":
            st.session_state.logs.append(f"⚠️ REVIEW {result['transaction_id']} | Risk={result['risk_score']:.2f}")

        st.session_state.i += 1

        # ==============================
        # LIVE DASHBOARD
        # ==============================
        with placeholder.container():

            df = pd.DataFrame(st.session_state.data)

            st.subheader("📊 Live SOC Dashboard")

            c1, c2, c3, c4 = st.columns(4)

            c1.metric("Processed", len(df))
            c2.metric("Blocked", len(df[df["decision"] == "BLOCK"]))
            c3.metric("Review", len(df[df["decision"] == "REVIEW"]))
            c4.metric("Approved", len(df[df["decision"] == "APPROVE"]))

            st.divider()

            # ================= ALERTS =================
            st.subheader("🚨 Auto Generated Alerts")

            for alert in st.session_state.logs[-10:]:
                st.write(alert)

            # ================= RISK TREND =================
            st.subheader("📈 Risk Trend")
            st.line_chart(df["risk_score"])

            # ================= TRANSACTION TABLE =================
            st.subheader("📄 Latest Transactions")
            st.dataframe(df.tail(10), use_container_width=True)

            # ================= HITL SECTION =================
            st.subheader("👤 Human-in-the-Loop Overrides")

            for row in df.tail(5).to_dict("records"):

                st.write(f"TXN {row['transaction_id']} | {row['decision']} | Risk {row['risk_score']:.2f}")

                colA, colB = st.columns(2)

                if colA.button(
                    "Approve Override",
                    key=f"approve_{row['transaction_id']}"
                ):
                    human_override(row["transaction_id"], "APPROVE")

                if colB.button(
                    "Block Override",
                    key=f"block_{row['transaction_id']}"
                ):
                    human_override(row["transaction_id"], "BLOCK")

            # ================= HUMAN ACTION LOG =================
            st.subheader("🧠 Override Log")
            st.write(st.session_state.human_actions[-10:])

        time.sleep(1.0)

else:
    st.info("Click ▶ Start Live Stream to begin agentic transaction processing.")
