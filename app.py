import streamlit as st
import pandas as pd
import numpy as np
import random
import time

# ---------------- SAFE SHAP IMPORT ----------------
try:
    import shap
    SHAP_AVAILABLE = True
except:
    SHAP_AVAILABLE = False


# ---------------- SESSION STATE ----------------
if "run_id" not in st.session_state:
    st.session_state.run_id = 0

if "actions" not in st.session_state:
    st.session_state.actions = {}

if "stream_running" not in st.session_state:
    st.session_state.stream_running = True


# ---------------- DATA GENERATION ----------------
def generate_data(n=50):
    data = []
    for i in range(n):
        amount = np.random.randint(100, 20000)
        velocity = np.random.randint(1, 50)
        deviation = np.random.random()

        risk = (
            (amount / 20000) * 0.4 +
            (velocity / 50) * 0.4 +
            deviation * 0.2
        )

        data.append({
            "transaction_id": f"T{i}",
            "amount": amount,
            "velocity": velocity,
            "deviation": round(deviation, 2),
            "risk_score": round(risk, 2)
        })

    return pd.DataFrame(data)


# ---------------- AGENT LOGIC ----------------
def fraud_agent(row):
    return row["risk_score"] > 0.7


def aml_agent(row):
    return row["velocity"] > 35


def fusion_agent(row):
    risk = row["risk_score"]
    if risk > 0.75:
        return "BLOCK"
    elif risk > 0.4:
        return "REVIEW"
    else:
        return "APPROVE"


# ---------------- SIMPLE GRAPH (NO LANGGRAPH BUGS) ----------------
class SimpleGraph:
    def invoke(self, state):
        row = state["transaction"]

        fraud_flag = fraud_agent(row)
        aml_flag = aml_agent(row)

        risk_score = row["risk_score"]

        decision = fusion_agent(row)

        # safe SHAP placeholder
        shap_score = risk_score * 100

        return {
            "fraud_flag": fraud_flag,
            "aml_flag": aml_flag,
            "risk_score": risk_score,
            "decision": decision,
            "shap_score": shap_score
        }


def build_graph():
    return SimpleGraph()


# ---------------- STREAMLIT UI ----------------
st.set_page_config(page_title="Financial Crime SOC", layout="wide")

st.title("🏦 Real-Time Financial Crime SOC (Agentic + HITL)")

app = build_graph()

df_placeholder = generate_data(50)

col1, col2, col3 = st.columns(3)

blocked = 0
review = 0
approve = 0

stream_box = st.empty()
log_box = st.empty()

# ---------------- LIVE STREAM ----------------
results = []

for idx, row in df_placeholder.iterrows():

    st.session_state.run_id += 1

    output = app.invoke({"transaction": row.to_dict()})

    row["decision"] = output["decision"]
    row["risk_score"] = output["risk_score"]

    results.append(row)

    # counters
    if row["decision"] == "BLOCK":
        blocked += 1
    elif row["decision"] == "REVIEW":
        review += 1
    else:
        approve += 1

    # ---------------- LIVE UI UPDATE ----------------
    with stream_box.container():

        st.subheader("📡 Live Agentic Stream")

        st.write(f"TOTAL: {len(results)}")
        st.write(f"BLOCKED: {blocked}")
        st.write(f"REVIEW: {review}")

        st.divider()

        for r in results[-15:]:  # last 15 only (prevents UI lag)

            color = "🚨" if r["decision"] == "BLOCK" else ("⚠️" if r["decision"] == "REVIEW" else "🟢")

            st.write(
                f"{color} {r['transaction_id']} | "
                f"{r['decision']} | Risk={r['risk_score']}"
            )

    # ---------------- SAFE SLEEP FOR LIVE EFFECT ----------------
    time.sleep(0.2)

# ---------------- FINAL SUMMARY ----------------
st.success("Live Agentic Stream Completed")

st.write({
    "TOTAL": len(results),
    "BLOCKED": blocked,
    "REVIEW": review,
    "APPROVE": approve
})
