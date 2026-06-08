import streamlit as st
import pandas as pd
import numpy as np
import time

# =========================
# OPTIONAL SHAP (SAFE)
# =========================
try:
    import shap
    SHAP_AVAILABLE = True
except Exception:
    shap = None
    SHAP_AVAILABLE = False


# =========================
# STREAMLIT CONFIG
# =========================
st.set_page_config(page_title="Financial Crime SOC", layout="wide")

st.title("🏦 Real-Time Financial Crime SOC (Agentic + HITL)")


# =========================
# SESSION STATE
# =========================
if "actions" not in st.session_state:
    st.session_state.actions = {}

if "stream_running" not in st.session_state:
    st.session_state.stream_running = True


# =========================
# DATA GENERATION
# =========================
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


# =========================
# AGENT LOGIC
# =========================
def fraud_agent(row):
    return row["risk_score"] > 0.7


def aml_agent(row):
    return row["velocity"] > 35


def fusion_agent(row):
    score = row["risk_score"]

    if score > 0.75:
        return "BLOCK"
    elif score > 0.40:
        return "REVIEW"
    else:
        return "APPROVE"


# =========================
# SIMPLE AGENT GRAPH (NO LANGGRAPH CRASH)
# =========================
class SimpleGraph:
    def invoke(self, state):
        row = state["transaction"]

        fraud = fraud_agent(row)
        aml = aml_agent(row)

        risk = row["risk_score"]
        decision = fusion_agent(row)

        shap_score = risk * 100  # safe placeholder

        return {
            "fraud_flag": fraud,
            "aml_flag": aml,
            "risk_score": risk,
            "decision": decision,
            "shap_score": shap_score
        }


def build_graph():
    return SimpleGraph()


app = build_graph()


# =========================
# UI PLACEHOLDERS
# =========================
stream_box = st.empty()
summary_box = st.empty()


# =========================
# DATA
# =========================
df = generate_data(50)

blocked = 0
review = 0
approve = 0

results = []


# =========================
# LIVE STREAM LOOP
# =========================
for i, row in df.iterrows():

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


    # =========================
    # LIVE DASHBOARD UPDATE
    # =========================
    with stream_box.container():

        st.subheader("📡 Live Transaction Stream")

        col1, col2, col3 = st.columns(3)
        col1.metric("BLOCKED", blocked)
        col2.metric("REVIEW", review)
        col3.metric("APPROVED", approve)

        st.divider()

        # show last 15 transactions only
        for r in results[-15:]:

            tag = "🚨" if r["decision"] == "BLOCK" else ("⚠️" if r["decision"] == "REVIEW" else "🟢")

            st.write(
                f"{tag} {r['transaction_id']} | "
                f"{r['decision']} | Risk={r['risk_score']:.2f}"
            )

    time.sleep(0.15)


# =========================
# FINAL SUMMARY
# =========================
with summary_box.container():
    st.success("Live Agentic Stream Completed")

    st.write({
        "TOTAL": len(results),
        "BLOCKED": blocked,
        "REVIEW": review,
        "APPROVED": approve,
        "SHAP_ENABLED": SHAP_AVAILABLE
    })
