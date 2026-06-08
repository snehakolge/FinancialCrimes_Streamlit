import streamlit as st
import pandas as pd
import time
from langgraph_engine import build_graph, generate_data

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(page_title="Financial Crime SOC", layout="wide")

st.title("🏦 Real-Time Financial Crime SOC (Agentic + HITL)")

# =====================================================
# SESSION STATE
# =====================================================
if "actions" not in st.session_state:
    st.session_state.actions = {}

if "stream_index" not in st.session_state:
    st.session_state.stream_index = 0


# =====================================================
# INIT ENGINE
# =====================================================
app = build_graph()
df = pd.DataFrame(generate_data(50))


# =====================================================
# RUN AGENTS (Batch simulation but streamed UI)
# =====================================================
results = []

for row in df.to_dict(orient="records"):

    output = app.invoke({
        "transaction": row,
        "fraud_score": 0,
        "aml_score": 0,
        "rbi_flags": [],
        "risk_score": 0,
        "decision": ""
    })

    results.append({**row, **output})

result_df = pd.DataFrame(results)


# =====================================================
# METRICS PANEL
# =====================================================
col1, col2, col3 = st.columns(3)

col1.metric("TOTAL TRANSACTIONS", len(result_df))
col2.metric("BLOCKED", len(result_df[result_df["decision"] == "BLOCK"]))
col3.metric("REVIEW", len(result_df[result_df["decision"] == "REVIEW"]))


st.divider()
st.subheader("📡 LIVE SOC STREAM (Real-Time Simulation)")


# =====================================================
# REAL LIVE STREAM ENGINE
# =====================================================
placeholder = st.empty()

actions_log = st.session_state.actions


# simulate continuous streaming behavior
for i in range(len(result_df)):

    row = result_df.iloc[i]

    with placeholder.container():

        st.markdown("### 🔴 Incoming Transaction Stream")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Txn ID", row["transaction_id"])
        c2.metric("Amount", row["amount"])
        c3.metric("Risk Score", round(row["risk_score"], 2))
        c4.metric("Decision", row["decision"])

        st.write("---")

        tx_id = row["transaction_id"]

        colA, colB = st.columns(2)

        # ---------------- APPROVE ----------------
        with colA:
            approve_key = f"approve_{tx_id}_{i}"

            if st.button("✔ Approve", key=approve_key):
                st.session_state.actions[tx_id] = "APPROVED"
                st.success(f"{tx_id} APPROVED by Analyst")

        # ---------------- BLOCK ----------------
        with colB:
            block_key = f"block_{tx_id}_{i}"

            if st.button("⛔ Block", key=block_key):
                st.session_state.actions[tx_id] = "BLOCKED"
                st.error(f"{tx_id} BLOCKED by Analyst")

        st.write("")

        # show current override if exists
        if tx_id in st.session_state.actions:
            st.info(f"Override: {st.session_state.actions[tx_id]}")

    time.sleep(0.6)


# =====================================================
# OVERRIDE LOG
# =====================================================
st.divider()
st.subheader("🧠 Human Override Log")

if st.session_state.actions:
    st.json(st.session_state.actions)
else:
    st.info("No overrides yet")


# =====================================================
# FINAL SUMMARY
# =====================================================
st.divider()
st.subheader("📊 Decision Breakdown")

st.bar_chart(
    result_df["decision"].value_counts()
)
