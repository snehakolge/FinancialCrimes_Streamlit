import streamlit as st
import pandas as pd
import numpy as np
import time
import shap
from sklearn.ensemble import RandomForestClassifier

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="SOC + SHAP", layout="wide")
st.title("Real-Time Financial Crime SOC (Agentic + HITL + SHAP)")

# ---------------------------
# STATE
# ---------------------------
if "override_log" not in st.session_state:
    st.session_state.override_log = {}

# ---------------------------
# DATA
# ---------------------------
def generate_data(n=50):
    np.random.seed(42)
    return pd.DataFrame({
        "amount": np.random.randint(100, 20000, n),
        "velocity": np.random.randint(1, 60, n),
        "failed_txn": np.random.randint(0, 2, n),
    })

df = generate_data(50)

# ---------------------------
# TRAIN SIMPLE MODEL (SIMULATED REAL ML)
# ---------------------------
X = df.copy()
y = ((X["amount"] > 12000) | (X["velocity"] > 40)).astype(int)

model = RandomForestClassifier(n_estimators=50, random_state=42)
model.fit(X, y)

# SHAP EXPLAINER
explainer = shap.TreeExplainer(model)

# ---------------------------
# AGENTS
# ---------------------------
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

# ---------------------------
# UI
# ---------------------------
col1, col2, col3 = st.columns(3)
t_box = col1.empty()
b_box = col2.empty()
r_box = col3.empty()

feed = st.empty()
explain_box = st.empty()

results = []

# ---------------------------
# LIVE STREAM
# ---------------------------
for i, row in df.iterrows():

    txn = pd.DataFrame([row])

    # ML prediction
    pred = model.predict(txn)[0]
    proba = model.predict_proba(txn)[0][1]

    # agents
    fraud = fraud_agent(row)
    aml = aml_agent(row)
    rbi_flags = rbi_agent(row)
    score = fusion(fraud, aml, rbi_flags)
    dec = decision(score)

    # SHAP explanation
    shap_values = explainer.shap_values(txn)[1][0]
    feature_names = txn.columns

    explanation = {
        feature_names[j]: float(shap_values[j])
        for j in range(len(feature_names))
    }

    results.append({
        "txn": f"T{i}",
        "score": score,
        "decision": dec,
        "ml_prob": proba
    })

    temp = pd.DataFrame(results)

    # counters
    total = len(temp)
    blocked = len(temp[temp["decision"] == "BLOCK"])
    review = len(temp[temp["decision"] == "REVIEW"])

    t_box.metric("TOTAL", total)
    b_box.metric("BLOCKED", blocked)
    r_box.metric("REVIEW", review)

    # LIVE FEED
    feed.markdown("## 📡 Live Agentic + ML Stream")

    for r in results[-10:]:
        icon = "🔴" if r["decision"] == "BLOCK" else "🟡" if r["decision"] == "REVIEW" else "🟢"
        feed.write(f"{icon} {r['txn']} | {r['decision']} | Risk={r['score']:.2f} | ML={r['ml_prob']:.2f}")

    # SHAP PANEL (LATEST TRANSACTION ONLY)
    explain_box.markdown("## 🧠 SHAP Explanation (Latest Transaction)")
    explain_box.json(explanation)

    st.toast(f"{dec} | Risk={score:.2f}")

    time.sleep(0.2)

st.success("SOC Stream Completed with SHAP Explainability")
