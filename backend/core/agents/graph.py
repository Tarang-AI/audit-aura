"""
LangGraph Workflow Orchestration
Multi-Agent Compliance Workflow
"""
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from datetime import datetime, timezone

from .state import GraphState
from .sensor import sensor_node
from .auditor import auditor_node
from .remediator import remediator_node
from .validator import validator_node
from .narrator import narrator_node
from .ticketer import create_incident_node, create_change_node, resolve_incident_node
from .logger import print_system_msg, log_agent_action
from .registry import upsert_incident


def route_after_auditor(state: GraphState) -> Literal["incident", "narrator", "__end__"]:
    """Route after auditor based on severity"""
    severity = state.get("severity", "None")
    
    if severity == "None":
        print_system_msg("Routing: No violation, going to END.")
        return "__end__"
    
    # Go to incident creation
    print_system_msg(f"Routing: Severity is {severity}, going to incident creation.")
    return "incident"


def route_after_validator(state: GraphState) -> Literal["remediator", "manual_fix", "resolve"]:
    """Route after validator based on validation status"""
    status = state.get("validation_status", "")
    retry_count = state.get("retry_count", 0)
    
    if status == "Failed":
        if retry_count >= 3:
            print_system_msg(f"Routing: Maximum retries ({retry_count}) reached. Escalating to Manual Fix.")
            return "manual_fix"
            
        print_system_msg(f"Routing: Validation Failed (Attempt {retry_count}), cycling back to Remediator.")
        return "remediator"
    
    print_system_msg("Routing: Validation Succeeded, going to resolve incident.")
    return "resolve"


def approval_node(state: GraphState) -> GraphState:
    """
    Mock approval node. In real use, this would be a placeholder for the interrupt.
    """
    msg = "Awaiting Human-in-the-Loop approval for Critical violation."
    log_agent_action("system", "Approval Required", msg)
    return {"execution_log": [{"node": "approval", "message": msg, "timestamp": datetime.now(timezone.utc).isoformat()}]}


def route_to_remediation(state: GraphState) -> Literal["approval", "remediator"]:
    """Route to remediation, with approval for critical issues"""
    severity = state.get("severity", "None")
    if severity == "Critical":
        print_system_msg("Routing: Critical severity detected. Redirecting to Approval.")
        return "approval"
    
    print_system_msg(f"Routing: {severity} severity. Proceeding to Auto-Remediation.")
    return "remediator"


def manual_fix_node(state: GraphState) -> GraphState:
    """
    Escalation node for manual remediation.
    """
    msg = "Autonomous remediation exhausted. Escalating for manual fix by security team."
    log_agent_action("system", "Manual Fix Required", msg)
    return {"execution_log": [{"node": "manual_fix", "message": msg, "timestamp": datetime.now(timezone.utc).isoformat()}]}


def build_graph():
    """
    Build the LangGraph workflow for compliance automation.
    
    Returns:
        StateGraph workflow ready to be compiled
    """
    # 1. Initialize StateGraph
    workflow = StateGraph(GraphState)
    
    # 2. Add Nodes (Agents)
    workflow.add_node("sensor", sensor_node)
    workflow.add_node("auditor", auditor_node)
    workflow.add_node("incident", create_incident_node)
    workflow.add_node("approval", approval_node)
    workflow.add_node("remediator", remediator_node)
    workflow.add_node("change", create_change_node)
    workflow.add_node("validator", validator_node)
    workflow.add_node("manual_fix", manual_fix_node)
    workflow.add_node("resolve", resolve_incident_node)
    workflow.add_node("narrator", narrator_node)
    
    # 3. Define Edges
    workflow.add_edge(START, "sensor")
    workflow.add_edge("sensor", "auditor")
    
    # Conditional edge after Auditor
    workflow.add_conditional_edges(
        "auditor",
        route_after_auditor,
        {
            "incident": "incident",
            "narrator": "narrator",
            "__end__": END
        }
    )
    
    # Conditional edge to either Approval or direct Remediation
    workflow.add_conditional_edges(
        "incident",
        route_to_remediation,
        {
            "approval": "approval",
            "remediator": "remediator"
        }
    )
    
    workflow.add_edge("approval", "remediator")
    workflow.add_edge("remediator", "change")
    workflow.add_edge("change", "validator")
    
    # Conditional edge after Validator (Cyclic Edge)
    workflow.add_conditional_edges(
        "validator",
        route_after_validator,
        {
            "remediator": "remediator", 
            "manual_fix": "manual_fix",
            "resolve": "resolve"
        }
    )
    
    # From manual fix, go back to validator for final verification
    workflow.add_edge("manual_fix", "validator")
    
    workflow.add_edge("resolve", "narrator")
    workflow.add_edge("narrator", END)
    
    return workflow


async def get_compiled_graph():
    """
    Get a compiled graph with async SQLite checkpointer.
    
    Returns:
        Compiled LangGraph application
    """
    from pathlib import Path
    
    # Ensure data directory exists
    Path("./data").mkdir(parents=True, exist_ok=True)
    
    checkpointer = AsyncSqliteSaver.from_conn_string("./data/checkpoints.sqlite")
    workflow = build_graph()
    
    # Compile with checkpointer and interrupt before approval
    graph_app = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["approval"]
    )
    
    return graph_app

# Made with Bob
