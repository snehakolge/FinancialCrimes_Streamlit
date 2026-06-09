import streamlit as st
import pandas as pd
import random
import time
import numpy as np

from typing import TypedDict
from langgraph.graph import StateGraph, END

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Financial Crime SOC",
    layout="wide"
)

st.title("🏦 Real-Time Financial Crime SOC (Agentic + LangGraph + HITL)")

# =========================================================
# SESSION STATE
# =========================================================

if "stats" not in st.session_state:

    st.session_state.stats = {
        "APPROVE": 0,
        "REVIEW": 0,
        "BLOCK": 0,
        "FREEZE": 0
    }

if "alerts" not in st.session_state:

    st.session_state.alerts = []

if "running" not in st.session_state:

    st.session_state.running = False

if "txn_counter" not in st.session_state:

    st.session_state.txn_counter = 0

if "customer_risk" not in st.session_state:

    st.session_state.customer_risk = {}

if "actions" not in st.session_state:

    st.session_state.actions = {}

if "model_metrics" not in st.session_state:

    st.session_state.model_metrics = {
        "precision": 95,
        "recall": 96,
        "f1": 95
    }

if "drift_score" not in st.session_state:

    st.session_state.drift_score = 0.12

if "retraining_log" not in st.session_state:

    st.session_state.retraining_log = []

# =========================================================
# PLACEHOLDERS
# =========================================================

metric_placeholder = st.empty()
feed_placeholder = st.empty()

# =========================================================
# TRANSACTION GENERATOR
# =========================================================

def generate_transaction():

    txn_id = f"T{st.session_state.txn_counter}"

    st.session_state.txn_counter += 1

    customer_id = f"C{random.randint(100,120)}"

    txn = {
        "txn_id": txn_id,
        "customer_id": customer_id,
        "amount": random.randint(100, 20000),
        "velocity": random.randint(1, 15),
        "device_change": random.choice([0,1]),
        "geo_risk": random.choice([0,1]),
        "behavioral_anomaly": random.choice([0,1]),
        "risk_score": 0.0,
        "reasons": [],
        "decision": "APPROVE"
    }

    return txn

# =========================================================
# LANGGRAPH STATE
# =========================================================

class FraudState(TypedDict):

    txn_id: str
    customer_id: str
    amount: int
    velocity: int
    device_change: int
    geo_risk: int
    behavioral_anomaly: int
    risk_score: float
    reasons: list
    decision: str

# =========================================================
# AGENTS
# =========================================================

def amount_agent(state):

    if state.get("amount",0) > 12000:

        state["risk_score"] += 0.4

        state["reasons"].append(
            "High Amount Spike"
        )

    return state


def velocity_agent(state):

    if state.get("velocity",0) > 8:

        state["risk_score"] += 0.3

        state["reasons"].append(
            "Velocity Breach"
        )

    return state


def device_agent(state):

    if state.get("device_change",0) == 1:

        state["risk_score"] += 0.2

        state["reasons"].append(
            "Device Change Detected"
        )

    return state


def geo_agent(state):

    if state.get("geo_risk",0) == 1:

        state["risk_score"] += 0.2

        state["reasons"].append(
            "High Risk Geography"
        )

    return state


def behavior_agent(state):

    if state.get("behavioral_anomaly",0) == 1:

        state["risk_score"] += 0.2

        state["reasons"].append(
            "Behavioral Anomaly"
        )

    return state


def memory_agent(state):

    customer = state.get("customer_id")

    old_risk = st.session_state.customer_risk.get(
        customer,
        0
    )

    # EARLIER RISK DETECTION

    if old_risk >= 1:

        state["risk_score"] += 0.2

        state["reasons"].append(
            "Repeat Risk Customer"
        )

    st.session_state.customer_risk[customer] = old_risk + 1

    return state


def decision_agent(state):

    risk = state["risk_score"]

    if risk >= 1.2:

        state["decision"] = "FREEZE"

    elif risk >= 0.8:

        state["decision"] = "BLOCK"

    elif risk >= 0.5:

        state["decision"] = "REVIEW"

    else:

        state["decision"] = "APPROVE"

    return state

# =========================================================
# LANGGRAPH WORKFLOW
# =========================================================

workflow = StateGraph(FraudState)

workflow.add_node("amount", amount_agent)

workflow.add_node("velocity", velocity_agent)

workflow.add_node("device", device_agent)

workflow.add_node("geo", geo_agent)

workflow.add_node("behavior", behavior_agent)

workflow.add_node("memory", memory_agent)

workflow.add_node("decision", decision_agent)

workflow.set_entry_point("amount")

workflow.add_edge("amount", "velocity")

workflow.add_edge("velocity", "device")

workflow.add_edge("device", "geo")

workflow.add_edge("geo", "behavior")

workflow.add_edge("behavior", "memory")

workflow.add_edge("memory", "decision")

workflow.add_edge("decision", END)

app = workflow.compile()

# =========================================================
# COMMAND CENTER METRICS
# =========================================================

with metric_placeholder.container():

    st.markdown(
        "## 🛡️ Autonomous Fraud Command Center"
    )

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "TOTAL",
        sum(st.session_state.stats.values())
    )

    c2.metric(
        "BLOCK",
        st.session_state.stats["BLOCK"]
    )

    c3.metric(
        "REVIEW",
        st.session_state.stats["REVIEW"]
    )

    c4.metric(
        "FREEZE",
        st.session_state.stats["FREEZE"]
    )

    c5.metric(
        "DRIFT SCORE",
        round(
            st.session_state.drift_score,
            2
        )
    )

# =========================================================
# CONTROL BUTTONS
# =========================================================

st.divider()

col1, col2 = st.columns(2)

with col1:

    if st.button("▶ Start Live Stream"):

        st.session_state.running = True

with col2:

    if st.button("⏹ Stop Stream"):

        st.session_state.running = False

# =========================================================
# LIVE TRANSACTION FLOW
# =========================================================

if st.session_state.running:

    txn = generate_transaction()

    # =====================================================
    # DRIFT SIMULATION
    # =====================================================

    st.session_state.drift_score += round(
        random.uniform(0.01,0.05),
        2
    )

    st.session_state.drift_score = min(
        st.session_state.drift_score,
        1.0
    )

    # =====================================================
    # MODEL PERFORMANCE DEGRADATION
    # =====================================================

    st.session_state.model_metrics["recall"] -= random.choice([0,1])

    st.session_state.model_metrics["precision"] -= random.choice([0,1])

    st.session_state.model_metrics["f1"] -= random.choice([0,1])

    # SAFE LIMITS

    st.session_state.model_metrics["recall"] = max(
        st.session_state.model_metrics["recall"],
        70
    )

    st.session_state.model_metrics["precision"] = max(
        st.session_state.model_metrics["precision"],
        70
    )

    st.session_state.model_metrics["f1"] = max(
        st.session_state.model_metrics["f1"],
        70
    )

    # =====================================================
    # RUN LANGGRAPH
    # =====================================================

    result = app.invoke(txn)

    decision = result["decision"]

    if decision not in st.session_state.stats:

        st.session_state.stats[decision] = 0

    st.session_state.stats[decision] += 1

    # =====================================================
    # STORE ALERTS
    # =====================================================

    st.session_state.alerts.insert(
        0,
        result
    )

    st.session_state.alerts = st.session_state.alerts[:15]

    # =====================================================
    # UPDATE METRICS
    # =====================================================

    with metric_placeholder.container():

        st.markdown(
            "## 🛡️ Autonomous Fraud Command Center"
        )

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric(
            "TOTAL",
            sum(st.session_state.stats.values())
        )

        c2.metric(
            "BLOCK",
            st.session_state.stats["BLOCK"]
        )

        c3.metric(
            "REVIEW",
            st.session_state.stats["REVIEW"]
        )

        c4.metric(
            "FREEZE",
            st.session_state.stats["FREEZE"]
        )

        c5.metric(
            "DRIFT SCORE",
            round(
                st.session_state.drift_score,
                2
            )
        )

    # =====================================================
    # LIVE FEED
    # =====================================================

    with feed_placeholder.container():

        st.subheader("🚨 Live AI Alert Feed")

        latest_alerts = st.session_state.alerts[:10]

        for idx, r in enumerate(latest_alerts):

            emoji = {
                "APPROVE": "🟢",
                "REVIEW": "⚠️",
                "BLOCK": "🚨",
                "FREEZE": "🧊"
            }

            st.markdown(
                f"""
### {emoji[r['decision']]} {r['decision']} | {r['txn_id']} | Risk={round(r['risk_score'],2)}

Reasons: {' | '.join(r['reasons'])}

Amount: ₹{r['amount']}

Customer: {r['customer_id']}
                """
            )

            action_key = f"{r['txn_id']}_{idx}_{r['decision']}"

            if r["decision"] in [
                "BLOCK",
                "REVIEW",
                "FREEZE"
            ]:

                if st.button(
                    f"Investigate {r['txn_id']}",
                    key=action_key
                ):

                    st.session_state.actions[
                        r["txn_id"]
                    ] = "Investigated"

    # =====================================================
    # STREAM SPEED
    # =====================================================

    time.sleep(2)

    st.rerun()

# =========================================================
# INVESTIGATOR ACTIONS
# =========================================================

st.divider()

st.subheader("📌 Investigator Actions")

if len(st.session_state.actions) > 0:

    actions_df = pd.DataFrame(
        list(st.session_state.actions.items()),
        columns=[
            "Transaction",
            "Status"
        ]
    )

    st.dataframe(
        actions_df,
        use_container_width=True
    )

else:

    st.info(
        "No investigations initiated yet."
    )

# =========================================================
# AI INVESTIGATION NARRATIVE
# =========================================================

st.divider()

st.subheader("🧠 AI Investigation Narrative")

if len(st.session_state.alerts) >= 1:

    latest_case = next(
        (
            a for a in st.session_state.alerts
            if a["decision"] in [
                "BLOCK",
                "REVIEW",
                "FREEZE"
            ]
        ),
        st.session_state.alerts[0]
    )

    narrative = f"""
🚨 Fraud Agent:
Detected suspicious transaction behavior.

🧠 Behavioral Agent:
Detected anomaly pattern.

👤 Memory Agent:
Customer historical risk evaluated.

⚖️ Decision Agent:
Recommended {latest_case['decision']} action.

📊 Risk Score:
{round(latest_case['risk_score'],2)}

📌 Reasons:
{' | '.join(latest_case['reasons'])}
"""

    st.text(narrative)

else:

    st.info(
        "No investigation narratives available."
    )

# =========================================================
# HIGH RISK CUSTOMERS
# =========================================================

st.divider()

st.subheader("📊 High Risk Customers")

risk_df = pd.DataFrame(
    list(
        st.session_state.customer_risk.items()
    ),
    columns=[
        "Customer",
        "Risk Count"
    ]
)

if not risk_df.empty:

    risk_df = risk_df.sort_values(
        by="Risk Count",
        ascending=False
    )

    st.dataframe(
        risk_df.head(10),
        use_container_width=True
    )

else:

    st.info(
        "No customer risk data yet."
    )

# =========================================================
# DECISION ANALYTICS
# =========================================================

st.divider()

st.subheader("📈 Decision Analytics")

chart_df = pd.DataFrame({

    "Decision": [
        "APPROVE",
        "REVIEW",
        "BLOCK",
        "FREEZE"
    ],

    "Count": [

        st.session_state.stats["APPROVE"],
        st.session_state.stats["REVIEW"],
        st.session_state.stats["BLOCK"],
        st.session_state.stats["FREEZE"]
    ]
})

st.dataframe(
    chart_df,
    use_container_width=True
)

st.bar_chart(
    chart_df.set_index("Decision")
)

# =========================================================
# CONTINUOUS MODEL EVALUATION
# =========================================================

st.divider()

st.subheader(
    "📈 Continuous AI Model Evaluation"
)

metric_df = pd.DataFrame({

    "Metric": [
        "Precision",
        "Recall",
        "F1"
    ],

    "Score": [

        st.session_state.model_metrics["precision"],
        st.session_state.model_metrics["recall"],
        st.session_state.model_metrics["f1"]
    ]
})

st.dataframe(
    metric_df,
    use_container_width=True
)

trend_df = pd.DataFrame({

    "Cycle": [
        "C1",
        "C2",
        "C3",
        "C4",
        "C5"
    ],

    "Recall": [
        96,
        94,
        92,
        89,
        st.session_state.model_metrics["recall"]
    ],

    "Precision": [
        95,
        94,
        93,
        91,
        st.session_state.model_metrics["precision"]
    ]
})

st.line_chart(
    data=trend_df,
    x="Cycle",
    y=["Recall", "Precision"]
)

# =========================================================
# DRIFT ALERTS
# =========================================================

if st.session_state.model_metrics["recall"] < 85:

    st.error(
        "🚨 AI ALERT: Fraud Recall Dropped"
    )

if st.session_state.drift_score > 0.40:

    st.warning(
        "⚠️ Drift Detection Agent Triggered"
    )

# =========================================================
# SELF-HEALING AGENT
# =========================================================

st.divider()

st.subheader("🤖 Self-Healing AI Agent")

if st.session_state.drift_score > 0.40:

    st.warning(
        "⚠️ Autonomous Retraining Pipeline Activated"
    )

    if st.button("Run AI Retraining"):

        with st.spinner(
            "Training New Fraud Model..."
        ):

            time.sleep(3)

            old_recall = st.session_state.model_metrics["recall"]

            new_recall = random.randint(90,97)

            st.session_state.model_metrics["recall"] = new_recall

            st.session_state.model_metrics["precision"] = random.randint(90,97)

            st.session_state.model_metrics["f1"] = random.randint(90,97)

            st.session_state.drift_score = round(
                random.uniform(0.05,0.25),
                2
            )

            retrain_result = {

                "Old Recall": old_recall,

                "New Recall": new_recall,

                "Status": "DEPLOYED"
            }

            st.session_state.retraining_log.append(
                retrain_result
            )

            st.success(
                "✅ Governance Agent Approved New Model"
            )

# =========================================================
# RETRAINING AUDIT LOG
# =========================================================

if len(st.session_state.retraining_log) > 0:

    st.subheader(
        "📜 Retraining Audit Log"
    )

    st.dataframe(
        pd.DataFrame(
            st.session_state.retraining_log
        ),
        use_container_width=True
    )

else:

    st.info(
        "No retraining events yet."
    )
