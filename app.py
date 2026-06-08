import streamlit as st
import pandas as pd
import numpy as np
import time

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="Financial Crime SOC", layout="wide")

st.title("Real-Time Financial Crime SOC (Agentic + HITL)")

# -----------------------------
# SESSION STATE INIT
# -----------------------------
if "override_log" not in st.session_state:
    st.session_state.override_log = {}

if "stream_running" not in st.session_state:
    st.session_state.stream_running = True


# -----------------------------
# SYNTHETIC DATA GENERATOR
# -----------------------------
def generate_data(n=50):
    np.random.seed(42)
    df = pd.DataFrame({
        "transaction_id": [f"T{i}" for i in range(n)],
        "amount": np.random.randint(100, 20000, n),
        "velocity_7d": np.random.randint(1, 50, n),
        "amount_deviation": np.random.random(n),
        "failed_txn_flag": np.random.randint(0, 2, n)
    })
    return df


# -----------------------------
# SIMPLE RISK ENGINE (AGENTIC SIMULATION)
# -----------------------------
def risk_engine(row):
    risk = (
        row["amount"] / 20000 * 0.4 +
        row["velocity_7d"] / 50 * 0.3 +
        row["amount_deviation"] * 0.2 +
        row["failed_txn_flag"] * 0.1
    )
    return float(min(1.0, risk))


def decision(risk):
    if risk >= 0.7:
        return "BLOCK"
    elif risk >= 0.4:
        return "REVIEW"
    else:
        return "APPROVE"


# -----------------------------
# STREAMING PLACEHOLDERS
# -----------------------------
col1, col2, col3 = st.columns(3)

total_box = col1.empty()
block_box = col2.empty()
review_box = col3.empty()

feed_box = st.empty()
override_box = st.empty()


# -----------------------------
# GENERATE DATA
# -----------------------------
df = generate_data(50)


# -----------------------------
# LIVE STREAM LOOP
# -----------------------------
results = []

for i, row in df.iterrows():

    risk = risk_engine(row)
    dec = decision(risk)

    results.append({
        "transaction_id": row["transaction_id"],
        "risk": round(risk, 2),
        "decision": dec
    })

    # update stats
    temp_df = pd.DataFrame(results)

    total = len(temp_df)
    blocked = len(temp_df[temp_df["decision"] == "BLOCK"])
    review = len(temp_df[temp_df["decision"] == "REVIEW"])

    total_box.metric("TOTAL", total)
    block_box.metric("BLOCKED", blocked)
    review_box.metric("REVIEW", review)

    # LIVE FEED
    feed_box.markdown("### 📡 Live Transaction Feed")

    for r in results[-15:]:
        color = "🔴" if r["decision"] == "BLOCK" else "🟡" if r["decision"] == "REVIEW" else "🟢"
        feed_box.write(
            f"{color} {r['transaction_id']} | "
            f"{r['decision']} | Risk={r['risk']}"
        )

    # OVERRIDE PANEL
    override_box.markdown("### 🧠 Human Override Log")
    override_box.json(st.session_state.override_log)

    # small delay for live effect
    time.sleep(0.2)

# -----------------------------
# FINAL SUMMARY
# -----------------------------
st.success("Stream Completed (Prototype Mode)")
