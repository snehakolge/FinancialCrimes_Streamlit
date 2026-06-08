import streamlit as st
import pandas as pd
import random
import time

from langgraph.graph import StateGraph, END

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(layout="wide")

st.title("🏦 Real-Time Financial Crime SOC (Agentic + LangGraph + HITL)")

# =========================================================
# SESSION STATE
# =========================================================

if "running" not in st.session_state:
    st.session_state.running = False

if "feed" not in st.session_state:
    st.session_state.feed = []

if "stats" not in st.session_state:
    st.session_state.stats = {
        "TOTAL": 0,
        "BLOCK": 0,
        "REVIEW": 0,
        "APPROVE": 0
    }

if "actions" not in st.session_state:
    st.session_state.actions = {}

# =========================================================
# GENERATE LIVE TRANSACTION
# =========================================================

def generate_txn(i):

    return {
        "txn_id": f"T{i}",
        "customer_id": f"C{random.randint(100,120)}",
        "amount": random.randint(100, 20000),
        "velocity": random.randint(1, 15),
        "device_change": random.choice([0,1]),
        "geo_risk": random.choice([0,1]),
        "behavior_score": round(random.uniform(0,1),2)
    }

# =========================================================
# FRAUD AGENT
# =========================================================

def fraud_agent(state):

    score = 0

    reasons = state.get("reasons", []).copy()

    amount = state.get("amount", 0)

    device_change = state.get("device_change", 0)

    if amount > 12000:

        score += 0.4

        reasons.append("High Amount Spike")

    if device_change == 1:

        score += 0.2

        reasons.append("Device Change Detected")

    return {
        **state,
        "fraud_score": score,
        "reasons": reasons
    }

# =========================================================
# AML AGENT
# =========================================================

def aml_agent(state):

    score = 0

    reasons = state.get("reasons", []).copy()

    velocity = state.get("velocity", 0)

    if velocity > 8:

        score += 0.4

        reasons.append("Velocity Breach")

    return {
        **state,
        "aml_score": score,
        "reasons": reasons
    }

# =========================================================
# BEHAVIOR AGENT
# =========================================================

def behavior_agent(state):

    score = 0

    reasons = state.get("reasons", []).copy()

    behavior_score = state.get("behavior_score", 0)

    if behavior_score > 0.7:

        score += 0.3

        reasons.append("Behavioral Anomaly")

    return {
        **state,
        "behavior_score_agent": score,
        "reasons": reasons
    }

# =========================================================
# GEO AGENT
# =========================================================

def geo_agent(state):

    score = 0

    reasons = state.get("reasons", []).copy()

    geo_risk = state.get("geo_risk", 0)

    if geo_risk == 1:

        score += 0.3

        reasons.append("High Risk Geography")

    return {
        **state,
        "geo_score": score,
        "reasons": reasons
    }

# =========================================================
# MEMORY AGENT
# =========================================================

def memory_agent(state):

    score = 0

    reasons = state.get("reasons", []).copy()

    repeat_risk = random.choice([0,1])

    if repeat_risk == 1:

        score += 0.2

        reasons.append("Repeat Risk Customer")

    return {
        **state,
        "memory_score": score,
        "reasons": reasons
    }

# =========================================================
# FUSION AGENT
# =========================================================

def fusion_agent(state):

    fraud_score = state.get("fraud_score", 0)

    aml_score = state.get("aml_score", 0)

    behavior_score_agent = state.get("behavior_score_agent", 0)

    geo_score = state.get("geo_score", 0)

    memory_score = state.get("memory_score", 0)

    risk = (
        fraud_score
        + aml_score
        + behavior_score_agent
        + geo_score
        + memory_score
    )

    if risk >= 0.8:

        decision = "BLOCK"

    elif risk >= 0.5:

        decision = "REVIEW"

    else:

        decision = "APPROVE"

    return {
        **state,
        "risk_score": round(risk,2),
        "decision": decision
    }

# =========================================================
# BUILD LANGGRAPH
# =========================================================

workflow = StateGraph(dict)

workflow.add_node("fraud", fraud_agent)

workflow.add_node("aml", aml_agent)

workflow.add_node("behavior", behavior_agent)

workflow.add_node("geo", geo_agent)

workflow.add_node("memory", memory_agent)

workflow.add_node("fusion", fusion_agent)

workflow.set_entry_point("fraud")

workflow.add_edge("fraud", "aml")

workflow.add_edge("aml", "behavior")

workflow.add_edge("behavior", "geo")

workflow.add_edge("geo", "memory")

workflow.add_edge("memory", "fusion")

workflow.add_edge("fusion", END)

app = workflow.compile()

# =========================================================
# CONTROL BUTTONS
# =========================================================

col1, col2 = st.columns(2)

with col1:

    if st.button("▶ Start Live Stream"):

        st.session_state.running = True

with col2:

    if st.button("⏹ Stop Stream"):

        st.session_state.running = False

# =========================================================
# METRICS
# =========================================================

c1, c2, c3 = st.columns(3)

c1.metric("TOTAL", st.session_state.stats["TOTAL"])

c2.metric("BLOCK", st.session_state.stats["BLOCK"])

c3.metric("REVIEW", st.session_state.stats["REVIEW"])

st.markdown("---")

# =========================================================
# LIVE FEED
# =========================================================

feed_placeholder = st.empty()

if st.session_state.running:

    txn_index = len(st.session_state.feed)

    txn = generate_txn(txn_index)

    result = app.invoke(txn)

    txn.update(result)

    st.session_state.feed.insert(0, txn)

    st.session_state.stats["TOTAL"] += 1

    decision = txn.get("decision", "APPROVE")

    if decision not in st.session_state.stats:

        st.session_state.stats[decision] = 0

    st.session_state.stats[decision] += 1

    with feed_placeholder.container():

        st.subheader("🚨 Live Feed")

        for idx, r in enumerate(st.session_state.feed[:12]):

            decision = r.get("decision", "APPROVE")

            risk_score = r.get("risk_score", 0)

            reasons = r.get("reasons", [])

            reason_text = " | ".join(reasons)

            if decision == "BLOCK":

                st.error(
                    f"""
🚨 BLOCK | {r.get('txn_id')} | Risk={risk_score}

Reasons: {reason_text}

Amount: ₹{r.get('amount')}

Customer: {r.get('customer_id')}
"""
                )

            elif decision == "REVIEW":

                st.warning(
                    f"""
⚠️ REVIEW | {r.get('txn_id')} | Risk={risk_score}

Reasons: {reason_text}

Amount: ₹{r.get('amount')}

Customer: {r.get('customer_id')}
"""
                )

            else:

                st.success(
                    f"""
🟢 APPROVE | {r.get('txn_id')} | Risk={risk_score}

Reasons: {reason_text}

Amount: ₹{r.get('amount')}

Customer: {r.get('customer_id')}
"""
                )

            unique_key = f"{r.get('txn_id')}_{idx}_{random.randint(1,9999999)}"

            st.button(
                f"Take Action {r.get('txn_id')}",
                key=unique_key
            )

    time.sleep(1)

    st.rerun()

# =========================================================
# INVESTIGATOR ACTIONS
# =========================================================

st.markdown("---")

st.subheader("📌 Investigator Actions")

st.write(st.session_state.actions)

# =========================================================
# HIGH RISK CUSTOMERS
# =========================================================

st.markdown("---")

st.subheader("📊 High Risk Customers")

risk_df = pd.DataFrame(st.session_state.feed)

if not risk_df.empty:

    if "risk_score" in risk_df.columns:

        high_risk = risk_df[
            risk_df["risk_score"] >= 0.8
        ][["customer_id", "risk_score", "txn_id"]]

        st.dataframe(high_risk, width="stretch")

# =========================================================
# DECISION ANALYTICS
# =========================================================

st.markdown("---")

st.subheader("📈 Decision Analytics")

analytics_df = pd.DataFrame([
    {
        "Decision": "BLOCK",
        "Count": st.session_state.stats["BLOCK"]
    },
    {
        "Decision": "REVIEW",
        "Count": st.session_state.stats["REVIEW"]
    },
    {
        "Decision": "APPROVE",
        "Count": st.session_state.stats["APPROVE"]
    }
])

st.bar_chart(
    analytics_df.set_index("Decision")
)

# =========================================================
# STATUS
# =========================================================

if st.session_state.running:

    st.success("🟢 Live Agentic Stream Running")

else:

    st.info("⏹ Stream Stopped")
