from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.agents.checkpoints import build_checkpointer
from app.agents.nodes import (
    AgentRuntime,
    calculate_score,
    deeper_scan,
    extract_details,
    fetch_url_content,
    generate_recommendation,
    human_review,
    receive_input,
    risk_gate,
    run_llm_analysis,
    run_rule_checks,
    run_web_verification,
    save_result,
)
from app.agents.state import PrismAgentState


def build_graph(runtime: AgentRuntime):
    workflow = StateGraph(PrismAgentState)

    workflow.add_node("receive_input", lambda state: receive_input(state, runtime))
    workflow.add_node("fetch_url_content", lambda state: fetch_url_content(state, runtime))
    workflow.add_node("extract_details", lambda state: extract_details(state, runtime))
    workflow.add_node("run_rule_checks", lambda state: run_rule_checks(state, runtime))
    workflow.add_node("run_web_verification", lambda state: run_web_verification(state, runtime))
    workflow.add_node("run_llm_analysis", lambda state: run_llm_analysis(state, runtime))
    workflow.add_node("calculate_score", lambda state: calculate_score(state, runtime))
    workflow.add_node("risk_gate", lambda state: risk_gate(state, runtime))
    workflow.add_node("human_review", lambda state: human_review(state, runtime))
    workflow.add_node("deeper_scan", lambda state: deeper_scan(state, runtime))
    workflow.add_node("generate_recommendation", lambda state: generate_recommendation(state, runtime))
    workflow.add_node("save_result", lambda state: save_result(state, runtime))

    workflow.add_edge(START, "receive_input")
    workflow.add_edge("receive_input", "fetch_url_content")
    workflow.add_edge("fetch_url_content", "extract_details")
    workflow.add_edge("extract_details", "run_rule_checks")
    workflow.add_edge("run_rule_checks", "run_web_verification")
    workflow.add_edge("run_web_verification", "run_llm_analysis")
    workflow.add_edge("run_llm_analysis", "calculate_score")
    workflow.add_edge("calculate_score", "risk_gate")

    workflow.add_conditional_edges(
        "risk_gate",
        lambda state: "human_review" if state.get("requires_human_review") else "generate_recommendation",
        {"human_review": "human_review", "generate_recommendation": "generate_recommendation"},
    )

    workflow.add_conditional_edges(
        "human_review",
        lambda state: "deeper_scan" if (state.get("human_decision") == "run_deeper_scan") else "generate_recommendation",
        {"deeper_scan": "deeper_scan", "generate_recommendation": "generate_recommendation"},
    )

    workflow.add_edge("deeper_scan", "calculate_score")
    workflow.add_edge("generate_recommendation", "save_result")
    workflow.add_edge("save_result", END)

    return workflow.compile(checkpointer=build_checkpointer(runtime.settings))


@lru_cache(maxsize=1)
def _cached_graph_key(_: int) -> None:
    return None
