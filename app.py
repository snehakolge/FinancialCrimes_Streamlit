import streamlit as st
import pandas as pd
import numpy as np
import time

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

# =========================
# STREAMLIT CONFIG
# =========================
st.set_page_config(page_title="Financial Crime SOC", layout="wide")

st.title("🏦 Real-Time Financial Crime SOC (ML + Agentic + HITL)")


# =========================
# SESSION STATE
# =========================
if "override_log" not in st.session_state:
    st.session_state.override_log = []


# =========================
# DATA GENERATION
# =========================
def generate_data(n=200):
    data = []

    for i in range(n):
        amount = np.random.randint(100, 20000)
        velocity = np.random.randint(1, 50)
        deviation = np.random.random()

        # synthetic label
        label = 1 if (amount > 16000 or velocity > 42 or deviation > 0.85) else 0

        data.append({
            "transaction_id": f"T{i}",
            "amount": amount,
            "velocity": velocity,
            "deviation": deviation,
            "label": label
        })

    return pd.DataFrame(data)


# =========================
# TRAIN MODEL (SAFE + FAST)
# =========================
@st.cache_resource
def train_model():
    df = generate_data(1000)

    X = df[["amount", "velocity", "deviation"]]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier(
        n_estimators=120,
        max_depth=6,
        random_state=42
    )

    model.fit(X_train, y_train)

    return model


model = train_model()


# =========================
# AGENTS
# =========================
def fraud_agent(prob):
    return prob


def aml_agent(row):
    return row["velocity"] > 38


def rbi_rules_agent(row):
    flags = []

    if row["amount"] > 15000:
        flags.append("HIGH_VALUE_TXN")

    if row["velocity"] > 40:
        flags.append("VELOCITY_SPIKE")

    if row["deviation"] > 0.8:
        flags.append("UNUSUAL_PATTERN")

    return flags


def decision_agent(prob, aml_flag, rbi_flags):
    score = prob

    if aml_flag:
        score += 0.1

    score += 0.05 * len(rbi_flags)

    if score > 0.85:
        return "BLOCK"
    elif score > 0.45:
        return "REVIEW"
    else:
        return "APPROVE"


# =========================
# GENERATE LIVE STREAM DATA
# =========================
df_stream = generate_data(50)


# =========================
# UI PLACEHOLDERS
# =========================
stream_box = st.empty()
summary_box = st.empty()

results = []

blocked = 0
review = 0
approve = 0


# =========================
# LIVE STREAM LOOP
# =========================
for i, row in df_stream.iterrows():

    X_input = pd.DataFrame([[
        row["amount"],
        row["velocity"],
        row["deviation"]
    ]], columns=["amount", "velocity", "deviation"])

    # ML probability
    fraud_prob = model.predict_proba(X_input)[0][1]

    # agents
    aml_flag = aml_agent(row)
    rbi_flags = rbi_rules_agent(row)

    decision = decision_agent
