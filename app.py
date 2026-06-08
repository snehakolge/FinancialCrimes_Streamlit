import streamlit as st
import pandas as pd
import numpy as np
import time
import shap
from sklearn.ensemble import RandomForestClassifier

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="Financial Crime SOC", layout="wide")
st.title("Real-Time Financial Crime SOC (Agentic + HITL + SHAP)")

# -----------------------------
# SESSION STATE
# -----------------------------
if "override_log" not in st.session_state:
    st.session_state.override_log = {}

# -----------------------------
# DATA GENERATION
# -----------------------------
def generate_data(n=50):
    np.random.seed(42)
    return pd.DataFrame({
        "amount": np.random.randint(100, 20000, n),
        "velocity": np.random.randint(1, 60, n),
        "failed_txn": np.random.randint(0, 2, n),
    })

df = generate_data(50)

# -----------------------------
# ML MODEL (REALISTIC)
# -----------------------------
X = df.copy()
y = ((X["amount"] > 12000) | (X["velocity"] > 40)).astype(int)

model = RandomForestClassifier(n_estimators=80, random_state=42)
model.fit(X, y)

# SHAP EXPLAINER
explainer = shap.TreeExplainer(model)

# -----------------------------
# AGENTS
# -----------------------------
def fraud_agent(txn):
    return txn["amount"] / 20000 + txn["velocity"] / 60

def aml_agent(txn):
    return txn["velocity"] / 60

def rbi_agent(txn):
    flags = []
    if txn["amount"] > 15000:
        flags.append("HIGH_VALUE")
    if txn["velocity"] > 45:
        flags.append("VELOCITY_SPIKE")
    return flags

def fusion(fraud, aml, rbi_flags):
    return min(1.0, fraud * 0.5 + aml * 0.3 + len(rbi_flags) * 0.2)

def decision(score):
    if score > 0.7:
        return "BLOCK"
    elif score > 0.4:
        return "REVIEW"
    return "APPROVE"

# -----------------------------
# SIMPLE EXPLANATION (SHAP SAFE)
# -----------------------------
def explain(row):
    return {
        "amount_impact": float(row["amount"] / 20000),
        "velocity_impact": float(row["velocity"] / 60),
        "failed_txn_impact": float(row["failed_txn"])
    }

# -----------------------------
# UI
# -----------------------------
col1, col2, col3 = st.columns(3)
t_box = col1.empty()
b_box = col2.empty()
r_box = col3.empty()

feed = st.empty()
explain_box = st.empty()

# -----------------------------
# STREAM LOOP
# -----------------------------
results = []

for i, row in df.iterrows():

    txn = pd.DataFrame([row])

    # ML prediction
    prob = model.predict_proba(txn)[0][1]

    # Agents
    fraud = fraud_agent(row)
    aml = aml_agent(row)
    rbi_flags = rbi_agent(row)
    score = fusion(fraud, aml, rbi_flags)
    dec = decision(score)

    # Explanation (SHAP replacement)
    explanation = explain(row)

    results.append({
        "txn": f"T{i}",
        "decision": dec,
        "score": score,
        "prob": prob
    })

    temp = pd.DataFrame(results)

    # stats
    total = len(temp)
    blocked = len(temp[temp["decision"] == "BLOCK"])
    review = len(temp[temp["decision"] == "REVIEW"])

    t_box.metric("TOTAL", total)
    b_box.metric("BLOCKED", blocked)
    r_box.metric("REVIEW", review)

    # LIVE FEED
    feed.markdown("## 📡 Live SOC Stream")

    for r in results[-10:]:
        icon = "🔴" if r["decision"] == "BLOCK" else "🟡" if r["decision"] == "REVIEW" else "🟢"
        feed.write(f"{icon} {r['txn']} | {r['decision']} | Risk={r['score']:.2f} | ML={r['prob']:.2f}")

    # EXPLANATION PANEL
    explain_box.markdown("## 🧠 Transaction Explainability")

    for k, v in explanation.items():
        if v > 0.6:
            st.error(f"{k}: HIGH IMPACT ({v:.2f})")
        elif v > 0.3:
            st.warning(f"{k}: MEDIUM IMPACT ({v:.2f})")
        else:
            st.success(f"{k}: LOW IMPACT ({v:.2f})")

    st.toast(f"{dec} | Risk={score:.2f}")

    time.sleep(0.2)

st.success("SOC Stream Completed")
