import streamlit as st
import pandas as pd
import random
import time
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

# ---------------- STREAMLIT ----------------
st.set_page_config(page_title="SOC AI Platform", layout="wide")
st.title("🏦 Real-Time Financial Crime SOC (Agentic + HITL)")

# ---------------- SYNTHETIC TRANSACTION ----------------
def generate_txn():
    return {
        "transaction_id": f"T{random.randint(1000,9999)}",
        "amount": random.randint(100, 120000),
        "velocity_7d": random.randint(1, 60),
        "failed_txn_flag": random.randint(0, 1),
        "merchant_risk": round(random.uniform(0.1, 0.95), 2),
    }

# ---------------- STATE ----------------
class State(TypedDict):
    transaction: dict
    fraud_score: float
    aml_score: float
    rbi_flags: List[str]
    risk_score: float
    decision: str

# ---------------- AGENTS ----------------

def fraud_agent(state: State):
    t = state["transaction"]
    score = 0

    if t["amount"] > 50000:
        score += 0.4
    if t["velocity_7d"] > 30:
        score += 0.3
    if t["failed_txn_flag"] == 1:
        score += 0.2

    return {"fraud_score": min(score, 1.0)}


def aml_agent(state: State):
    t = state["transaction"]
    score = 0

    if t["amount"] < 3000:
        score += 0.5
    if t["merchant_risk"] > 0.7:
        score += 0.3

    return {"aml_score": min(score, 1.0)}


def rbi_agent(state: State):
    t = state["transaction"]
    flags = []

    if t["velocity_7d"] > 25:
        flags.append("EWS_VELOCITY")
    if t["amount"] > 100000:
        flags.append("HIGH_VALUE")

    return {"rbi_flags": flags}


def fusion_agent(state: State):
    fraud = state.get("fraud_score", 0)
    aml = state.get("aml_score", 0)
    flags = state.get("rbi_flags", [])

    risk = fraud * 0.5 + aml * 0.4 + len(flags) * 0.1

    return {"risk_score": risk}


def decision_agent(state: State):
    r = state.get("risk_score", 0)

    if r < 0.3:
        decision = "APPROVE"
    elif r < 0.7:
        decision = "REVIEW"
    else:
        decision = "BLOCK"

    return {"decision": decision}

# ---------------- ROUTER ----------------
def router(state: State):
    t = state["transaction"]

    route = []

    if t["amount"] > 50000 or t["velocity_7d"] > 30:
        route.append("fraud")

    if t["amount"] < 3000 or t["merchant_risk"] > 0.7:
        route.append("aml")

    if not route:
        route.append("fraud")

    return {"route": route}

# ---------------- LANGGRAPH ----------------
def build_graph():
    g = StateGraph(State)

    g.add_node("router", router)
    g.add_node("fraud", fraud_agent)
    g.add_node("aml", aml_agent)
    g.add_node("rbi", rbi_agent)
    g.add_node("fusion", fusion_agent)
    g.add_node("decision", decision_agent)

    g.set_entry_point("router")

    g.add_conditional_edges("router", lambda s: s["route"])

    g.add_edge("fraud", "rbi")
    g.add_edge("aml", "rbi")
    g.add_edge("rbi", "fusion")
    g.add_edge("fusion", "decision")
    g.add_edge("decision", END)

    return g.compile()

app = build_graph()

# ---------------- SESSION STATE (LIVE STREAM CONTROL) ----------------
if "logs" not in st.session_state:
    st.session_state.logs = []

if "running" not in st.session_state:
    st.session_state.running = False

# ---------------- UI BUTTONS ----------------
col1, col2 = st.columns(2)

with col1:
    if st.button("▶ Start Live SOC Stream"):
        st.session_state.running = True

with col2:
    if st.button("⛔ Stop Stream"):
        st.session_state.running = False

placeholder = st.empty()

# ---------------- LIVE LOOP (CONTROLLED) ----------------
if st.session_state.running:

    for i in range(20):  # controlled streaming (safe for Streamlit)

        txn = generate_txn()

        result = app.invoke({"transaction": txn})

        record = {
            **txn,
            "fraud_score": result.get("fraud_score", 0),
            "aml_score": result.get("aml_score", 0),
            "risk_score": result.get("risk_score", 0),
            "decision": result.get("decision", "UNKNOWN")
        }

        st.session_state.logs.append(record)

        df = pd.DataFrame(st.session_state.logs)

        with placeholder.container():

            st.metric("Live Transactions", len(df))

            col1, col2, col3 = st.columns(3)

            col1.metric("BLOCKED", len(df[df["decision"] == "BLOCK"]))
            col2.metric("REVIEW", len(df[df["decision"] == "REVIEW"]))
            col3.metric("APPROVED", len(df[df["decision"] == "APPROVE"]))

            st.subheader("📊 Risk Trend")
            st.line_chart(df["risk_score"])

            st.subheader("🚨 Live Alerts")

            latest = df.tail(10)
            st.dataframe(latest)

            # ---------------- HUMAN-IN-THE-LOOP ----------------
            for _, row in latest.iterrows():

                if row["decision"] == "BLOCK":
                    st.error(
                        f"🚨 AUTO FRAUD ALERT | TXN {row['transaction_id']} | Risk {row['risk_score']:.2f}"
                    )

                    st.button(f"👤 Approve Override {row['transaction_id']}")

                elif row["decision"] == "REVIEW":
                    st.warning(
                        f"⚠️ HUMAN REVIEW REQUIRED | TXN {row['transaction_id']} | Risk {row['risk_score']:.2f}"
                    )

        time.sleep(1)

else:
    st.info("Click ▶ Start Live SOC Stream to begin agentic monitoring.")
