from typing import TypedDict, List
from langgraph.graph import StateGraph, END


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
    if t["merchant_risk"] > 0.6:
        score += 0.3

    return {"aml_score": min(score, 1.0)}


def rbi_agent(state: State):
    t = state["transaction"]
    flags = []

    if t["velocity_7d"] > 25:
        flags.append("EWS_VELOCITY_SPIKE")
    if t["amount"] > 100000:
        flags.append("HIGH_VALUE_ALERT")

    return {"rbi_flags": flags}


def fusion_agent(state: State):
    return {
        "risk_score": (
            state["fraud_score"] * 0.5 +
            state["aml_score"] * 0.4 +
            len(state["rbi_flags"]) * 0.1
        )
    }


def decision_agent(state: State):
    r = state["risk_score"]

    if r < 0.3:
        decision = "APPROVE"
    elif r < 0.7:
        decision = "REVIEW"
    else:
        decision = "BLOCK"

    return {"decision": decision}


# ---------------- GRAPH ----------------

def build_graph():
    workflow = StateGraph(State)

    workflow.add_node("fraud", fraud_agent)
    workflow.add_node("aml", aml_agent)
    workflow.add_node("rbi", rbi_agent)
    workflow.add_node("fusion", fusion_agent)
    workflow.add_node("decision", decision_agent)

    workflow.set_entry_point("fraud")

    workflow.add_edge("fraud", "aml")
    workflow.add_edge("aml", "rbi")
    workflow.add_edge("rbi", "fusion")
    workflow.add_edge("fusion", "decision")
    workflow.add_edge("decision", END)

    return workflow.compile()
