import streamlit as st
import pandas as pd
import numpy as np
import time

from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(page_title="Financial Crime SOC", layout="wide")

st.title("🏦 Real-Time Financial Crime SOC (ML + Agentic + HITL)")


# ==============================
# SESSION STATE
# ==============================
if "model" not in st.session_state:
    st.session_state.model = None

if "override_log" not in st.session_state:
    st.session_state.override_log = []

if "running" not in st.session_state:
    st.session_state.running = True


# ==============================
# DATA GENERATION (SIMULATION)
# ==============================
def generate_data(n=200):
    data = []

    for i in range(n):
        amount = np.random.randint(100, 20000)
        velocity = np.random.randint(1, 50)
        deviation = np.random.random()

        # synthetic label (for training)
        label = 1 if (amount > 15000 or velocity > 40 or deviation > 0.8) else 0

        data.append({
            "transaction_id": f"T{i}",
            "amount": amount,
            "velocity": velocity,
            "deviation": deviation,
            "label": label
        })

    return pd.DataFrame(data)


# ==============================
# TRAIN ML MODEL
# ==============================
@st.cache_resource
def train_model():
    df = generate_data(1000)

    X = df[["amount", "velocity", "deviation"]]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model = XGBClassifier(
        n_estimators=50,
        max_depth=4,
        learning_rate=0.1,
        eval_metric="logloss"
    )

    model.fit(X_train, y_train)

    return model


# ==============================
# AGENT LOGIC
# ==============================
def fraud_agent(prob):
    return prob


def aml_agent(row):
    return row["velocity"] > 35


def decision_agent(prob):
    if prob > 0.8:
        return "BLOCK"
    elif prob > 0.4:
        return "REVIEW"
    else:
        return "APPROVE"


def fusion_agent(prob, aml_flag):
    risk = prob + (0.1 if aml_flag else 0)

    if risk > 0.85:
        return "BLOCK"
    elif risk > 0.5:
        return "REVIEW"
    else:
        return "APPROVE"


# ==============================
# LOAD MODEL
# ==============================
model = train_model()


# ==============================
# STREAM DATA
# ==============================
df_stream = generate_data(50)

col1, col2, col3 = st.columns(3)

block_count = 0
review_count = 0
approve_count = 0

stream_box = st.empty()
override_box = st.empty()


results = []


# ==============================
# LIVE STREAM LOOP
# ==============================
for i, row in df_stream.iterrows():

    X_input = pd.DataFrame([[
        row["amount"],
        row["velocity"],
        row["deviation"]
    ]], columns=["amount", "velocity", "deviation"])

    # ML PREDICTION
    fraud_prob = model.predict_proba(X_input)[0][1]

    # AG
