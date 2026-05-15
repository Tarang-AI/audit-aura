"""
Remediator Agent - Automated Fix Execution
"""
import subprocess
import os
from datetime import datetime, timezone
from pathlib import Path

from .state import GraphState
from .logger import log_agent_action


def remediator_node(state: GraphState) -> GraphState:
    """
    The Remediation Agent node. Executes scripts to fix violations.
    
    Args:
        state: Current graph state with evaluation results
        
    Returns:
        Updated state with remediation action results
    """
    evaluations = state.get("evaluations", [])
    if not evaluations:
        return {"remediation_action": "None", "execution_log": []}
        
    latest_eval = evaluations[-1]
    recommended_action = latest_eval.get("RecommendedAction", "close_s3_bucket.py")
    
    if recommended_action == "None":
        return {"remediation_action": "None", "execution_log": []}

    script_path = Path("./scripts") / recommended_action
    action_taken = "None"
    status = "Success"
    msg = ""
    
    if script_path.exists():
        try:
            result = subprocess.run(
                ["python", str(script_path)],
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )
            msg = f"Applied fix via {recommended_action}. Output: {result.stdout.strip()[:100]}..."
            log_agent_action("remediator", "Fix Applied", msg)
            action_taken = f"Executed {recommended_action} successfully."
        except subprocess.CalledProcessError as e:
            msg = f"Failed to apply fix via {recommended_action}: {e.stderr}"
            log_agent_action("remediator", "Execution Failed", msg)
            action_taken = f"Failed to execute {recommended_action}."
            status = "Failed"
        except subprocess.TimeoutExpired:
            msg = f"Script {recommended_action} timed out after 30 seconds."
            log_agent_action("remediator", "Timeout", msg)
            action_taken = f"Timeout executing {recommended_action}."
            status = "Failed"
    else:
        msg = f"Script {recommended_action} not found. Mocking success."
        log_agent_action("remediator", "Mock Fix", msg)
        action_taken = f"Mock Executed {recommended_action}"

    execution_entry = {
        "node": "remediator",
        "message": msg,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": {"script": recommended_action, "status": status}
    }
        
    return {
        "remediation_action": action_taken,
        "execution_log": [execution_entry]
    }

# Made with Bob
