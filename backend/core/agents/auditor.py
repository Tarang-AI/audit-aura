"""
Auditor Agent - Compliance Evaluation and Violation Detection
"""
import os
import json
import chromadb
from datetime import datetime, timezone
from typing import Dict, Any, List
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from pathlib import Path

from .state import GraphState
from .logger import log_agent_action
from .registry import upsert_incident
from .llm_config import get_llm


class IndividualEvaluation(BaseModel):
    """Schema for individual log evaluation"""
    LogIndex: int = Field(description="The index of the log in the provided list.")
    Thought: str = Field(description="Step-by-step reasoning explaining the compliance check.")
    ViolationDetected: bool = Field(description="True if a violation was detected.")
    Severity: str = Field(description="Severity: 'None', 'Low', 'Medium', 'Critical'.")
    Framework: str = Field(description="Compliance Framework: 'SOC2', 'HIPAA', 'C5', or 'Internal'.")
    MappedControls: List[str] = Field(description="List of EXACT control IDs identified (e.g., 'CC6.1', 'AC-2').")
    RecommendedAction: str = Field(description="Remediation script filename, or 'None'.")


class BulkAuditorEvaluation(BaseModel):
    """Schema for bulk evaluation response"""
    Evaluations: List[IndividualEvaluation] = Field(description="A list of evaluations for each log.")


def get_relevant_controls(logs_text: str) -> str:
    """
    Queries ChromaDB for controls relevant to the entire batch of logs.
    
    Args:
        logs_text: Combined text of all logs
        
    Returns:
        Relevant control descriptions
    """
    try:
        # Ensure chroma_db directory exists
        chroma_path = Path("./data/chroma_db")
        chroma_path.mkdir(parents=True, exist_ok=True)
        
        client = chromadb.PersistentClient(path=str(chroma_path))
        collection = client.get_or_create_collection(name="compliance_controls")
        
        # If collection is empty, return default controls
        if collection.count() == 0:
            return """
            SOC2 CC6.1: Access controls restrict logical access to information assets
            SOC2 CC6.6: Transmission of data is protected
            SOC2 CC7.2: System monitoring detects and responds to security incidents
            HIPAA 164.308: Administrative safeguards
            HIPAA 164.312: Technical safeguards
            """
        
        results = collection.query(query_texts=[logs_text], n_results=5)
        
        controls = []
        if results and results['documents']:
            for doc in results['documents'][0]:
                controls.append(doc)
        return "\n".join(controls) if controls else "No specific controls found"
    except Exception as e:
        log_agent_action("auditor", "ChromaDB Error", f"Failed to query controls: {e}")
        return "Default compliance controls will be used"


def perform_bulk_audit(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Utility function to perform a bulk audit using the LLM.
    Used by the API to efficiently process logs before splitting into incidents.
    
    Args:
        logs: List of log entries to audit
        
    Returns:
        List of evaluation results
    """
    try:
        llm = get_llm(temperature=0.1)
        parser = JsonOutputParser(pydantic_object=BulkAuditorEvaluation)
        
        # Get available remediation scripts
        scripts_dir = Path("./scripts")
        available_scripts = []
        if scripts_dir.exists():
            available_scripts = [f.name for f in scripts_dir.glob("*.py")]
        scripts_list_str = ", ".join(available_scripts) if available_scripts else "None"
        
        prompt = PromptTemplate(
            template="""You are an expert Cloud Compliance Auditor.
Review the following list of logs against the provided compliance controls.

Use ReAct reasoning to evaluate EACH log individually.

CRITICAL INSTRUCTIONS:
1. If NO violation is detected for a log, set ViolationDetected=False.
2. If a violation is detected, select the most appropriate remediation script from the list.
3. For 'shadow-it' or 'unmanaged' resources that seem suspicious or persistent, USE 'fail_script.py' to trigger an escalation workflow.
4. Be specific about which Control IDs are violated.

Available Scripts: [{scripts_list}]

Controls:
{controls}

Logs to Audit:
{log_data}

{format_instructions}
""",
            input_variables=["controls", "log_data", "scripts_list"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        
        logs_str = "\n".join([f"Log {i}: {json.dumps(l)}" for i, l in enumerate(logs)])
        controls_text = get_relevant_controls(logs_str)
        
        chain = prompt | llm | parser
        result = chain.invoke({
            "controls": controls_text,
            "log_data": logs_str,
            "scripts_list": scripts_list_str
        })
        
        # Convert Pydantic models to dicts
        evaluations = result.get("Evaluations", [])
        return [eval_item.dict() if hasattr(eval_item, 'dict') else eval_item for eval_item in evaluations]
        
    except Exception as e:
        log_agent_action("auditor", "Bulk Audit Error", f"Failed to perform audit: {e}")
        return []


def auditor_node(state: GraphState) -> GraphState:
    """
    The Auditor Agent node. Processes logs to identify violations.
    If evaluations are already present (from API split), it uses them.
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with evaluation results
    """
    evaluations = state.get("evaluations", [])
    logs = state.get("logs", [])
    
    # If no evaluations present, perform audit (fallback/standalone mode)
    if not evaluations and logs:
        evaluations = perform_bulk_audit(logs)
    
    execution_entries = []
    violations = []
    
    for ev in evaluations:
        idx = ev.get("LogIndex", 0)
        if ev.get("ViolationDetected"):
            violations.append(ev)
            msg = f"Violation Found: {ev.get('Severity')} - {ev.get('Thought')[:150]}..."
            log_agent_action("auditor", "Violation Detected", msg)
        else:
            msg = f"Compliance Pass: {ev.get('Thought')[:100]}..."
            log_agent_action("auditor", "Pass", msg)
            
        execution_entries.append({
            "node": "auditor",
            "message": msg,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": ev
        })

    # Determine overall status and highest severity
    highest_severity = "None"
    offending_entity = "unknown"
    mapped_controls = []
    framework = "Internal"
    
    if violations:
        sev_map = {"Critical": 3, "Medium": 2, "Low": 1, "None": 0}
        violations.sort(key=lambda x: sev_map.get(x.get("Severity", "None"), 0), reverse=True)
        highest_severity = violations[0].get("Severity")
        framework = violations[0].get("Framework", "Internal")
        
        top_idx = violations[0].get("LogIndex", 0)
        top_log = logs[top_idx] if top_idx < len(logs) else {}
        
        # Robust entity extraction
        offending_entity = (
            top_log.get("resource_id") or 
            top_log.get("resource") or 
            top_log.get("user_identity") or 
            top_log.get("user") or 
            "unknown"
        )
        
        for v in violations:
            mapped_controls.extend(v.get("MappedControls", []))

    # Update incident registry
    incident_id = state.get("incident_id")
    if incident_id:
        status = "Closed"
        if highest_severity == "Critical":
            status = "Waiting for Approval"
        elif highest_severity != "None":
            status = "In Progress"
            
        upsert_incident(
            incident_id=incident_id,
            status=status,
            severity=highest_severity,
            offending_entity=offending_entity,
            mapped_controls=list(set(mapped_controls)),
            execution_history=state.get("execution_log", []) + execution_entries
        )
            
    return {
        "evaluations": violations,
        "severity": highest_severity,
        "offending_entity": offending_entity,
        "mapped_controls": list(set(mapped_controls)),
        "framework": framework,
        "control_id": mapped_controls[0] if mapped_controls else None,
        "execution_log": execution_entries
    }

# Made with Bob
