"""
Narrator Agent - Evidence Report Generation
"""
import os
import json
from datetime import datetime, timezone
from pathlib import Path
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from .state import GraphState
from .logger import log_agent_action
from .llm_config import get_llm


def narrator_node(state: GraphState) -> GraphState:
    """
    The Narrator Agent node. Generates and PERSISTS a comprehensive Evidence Report.
    
    Args:
        state: Current graph state with complete incident information
        
    Returns:
        Updated state with narrative report
    """
    try:
        llm = get_llm(temperature=0.7)
        
        incident_id = state.get("incident_id", "Unknown")
        logs = state.get("logs", [])
        full_logs_str = json.dumps(logs, indent=2)
        
        retry_count = state.get("retry_count", 0)
        validation_status = state.get("validation_status", "Unknown")
        
        # If it failed after retries, customize the prompt
        final_status = validation_status
        if validation_status == "Failed" and retry_count >= 3:
            final_status = "FAILED - Needs manual remediation"

        prompt = PromptTemplate(
            template="""You are a Senior Compliance Auditor and Forensic Expert.
Generate a professional, high-fidelity 'Incident Evidence Report' in Markdown format.

**Incident ID:** {incident_id}
**Entity:** {offending_entity}
**Severity:** {severity}
**Framework:** {audit_type}
**Controls:** {controls}
**Final Status:** {final_status}

**Description:**
{description}

**Detection Time:** {when_detected}

**Remediation Action:** {remediation_action}

**Change Ticket:** {change_ticket}

**Validation Status:** {validation_status}

**Retry Count:** {retry_count}

Write a comprehensive forensic report that includes:
1. Executive Summary
2. Technical Details
3. Compliance Impact
4. Remediation Steps Taken
5. Validation Results
6. Recommendations

Keep the report professional and suitable for audit purposes.
""",
            input_variables=[
                "incident_id", "offending_entity", "severity", "audit_type",
                "controls", "final_status", "description", "when_detected",
                "remediation_action", "change_ticket", "validation_status", "retry_count"
            ]
        )
        
        evals = state.get("evaluations", [])
        latest_eval = evals[-1] if evals else {}
        
        audit_type = latest_eval.get("Framework", "Internal")
        controls = ", ".join(latest_eval.get("MappedControls", ["Unknown"]))
        description = latest_eval.get("Thought", "Compliance violation detected.")
        
        first_log = logs[0] if logs else {}
        when_detected = first_log.get("timestamp", datetime.now(timezone.utc).isoformat())

        chain = prompt | llm | StrOutputParser()
        
        narrative = chain.invoke({
            "incident_id": incident_id,
            "final_status": final_status,
            "audit_type": audit_type,
            "controls": controls,
            "description": description,
            "offending_entity": state.get("offending_entity", "Unknown"),
            "severity": state.get("severity", "Unknown"),
            "when_detected": when_detected,
            "remediation_action": state.get("remediation_action", "None"),
            "change_ticket": state.get("change_ticket_id", "None"),
            "retry_count": retry_count,
            "validation_status": state.get("validation_status", "Unknown")
        })
        
        # Save the physical evidence file
        evidence_dir = Path("./data/evidence")
        evidence_dir.mkdir(parents=True, exist_ok=True)
        file_path = evidence_dir / f"{incident_id}.md"
        
        with open(file_path, "w") as f:
            f.write(narrative)
            
        log_agent_action("narrator", "Evidence Persisted", f"Full report saved to {file_path}")
        
    except Exception as e:
        narrative = f"Failed to generate narrative: {e}"
        log_agent_action("narrator", "Error", narrative)
        file_path = None

    execution_entry = {
        "node": "narrator",
        "message": f"Compliance evidence report persisted for {incident_id}.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": {"file": str(file_path) if file_path else "N/A"}
    }
        
    return {
        "narrative": narrative,
        "execution_log": [execution_entry]
    }

# Made with Bob
