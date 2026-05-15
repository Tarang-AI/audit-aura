"""
Remediation Approval Router
API endpoints for managing remediation approvals
"""
import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field

from core.detection.skills.remediation.approval_based_remediation import ApprovalBasedRemediationSkill
from infrastructure.messaging.websocket import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/remediations", tags=["remediations"])

# Global remediation skill instance
_remediation_skill: Optional[ApprovalBasedRemediationSkill] = None


def get_remediation_skill() -> ApprovalBasedRemediationSkill:
    """Get or create global remediation skill instance"""
    global _remediation_skill
    if _remediation_skill is None:
        _remediation_skill = ApprovalBasedRemediationSkill()
    return _remediation_skill


# Request/Response Models
class ApprovalDecision(BaseModel):
    """Model for approval decision"""
    action: str = Field(..., description="Action to take: approve_automated, approve_manual, approve_scheduled, reject, request_more_info")
    approver: str = Field(..., description="Name or ID of approver")
    comments: Optional[str] = Field(None, description="Approval comments or justification")
    scheduled_time: Optional[str] = Field(None, description="Scheduled execution time (ISO format) for approve_scheduled action")


class RemediationListResponse(BaseModel):
    """Response model for listing remediations"""
    remediations: List[dict] = Field(default_factory=list, description="List of pending remediations")
    total: int = Field(..., description="Total number of remediations")
    pending: int = Field(..., description="Number of pending remediations")
    approved: int = Field(..., description="Number of approved remediations")
    rejected: int = Field(..., description="Number of rejected remediations")


class RemediationDetailResponse(BaseModel):
    """Response model for remediation details"""
    approval_request: dict = Field(..., description="Approval request details")
    violation_details: dict = Field(..., description="Violation details")
    analysis_data: dict = Field(..., description="Analysis data")
    created_at: str = Field(..., description="Creation timestamp")


class ApprovalResponse(BaseModel):
    """Response model for approval action"""
    success: bool = Field(..., description="Whether action was successful")
    message: str = Field(..., description="Response message")
    remediation_id: str = Field(..., description="Remediation ID")
    status: str = Field(..., description="New status")
    execution_details: Optional[dict] = Field(None, description="Execution details if automated")


@router.get("/pending", response_model=RemediationListResponse)
async def list_pending_remediations():
    """
    List all pending remediation approvals
    
    Returns list of remediations awaiting admin approval
    """
    try:
        skill = get_remediation_skill()
        pending_remediations = skill.get_pending_remediations()
        
        # Count by status
        pending_count = sum(
            1 for r in pending_remediations.values()
            if r['request']['status'] == 'pending'
        )
        approved_count = sum(
            1 for r in pending_remediations.values()
            if r['request']['status'] in ['approved', 'approved_automated', 'approved_manual', 'approved_scheduled']
        )
        rejected_count = sum(
            1 for r in pending_remediations.values()
            if r['request']['status'] == 'rejected'
        )
        
        # Format remediations for response
        remediations_list = []
        for rem_id, rem_data in pending_remediations.items():
            request = rem_data['request']
            remediations_list.append({
                'id': rem_id,
                'status': request['status'],
                'bucket_name': request['violation_summary']['bucket_name'],
                'drift_type': request['violation_summary']['drift_type'],
                'risk_score': request['impact_summary']['risk_score'],
                'priority': request['impact_summary']['priority'],
                'created_at': request['created_at'],
                'expires_at': request['expires_at'],
                'requires_approval': True,
                'automation_available': request['remediation_details']['automation_available']
            })
        
        # Sort by risk score (highest first) and creation time
        remediations_list.sort(
            key=lambda x: (-x['risk_score'], x['created_at']),
            reverse=False
        )
        
        return RemediationListResponse(
            remediations=remediations_list,
            total=len(pending_remediations),
            pending=pending_count,
            approved=approved_count,
            rejected=rejected_count
        )
        
    except Exception as e:
        logger.error(f"Error listing remediations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list remediations: {str(e)}")


@router.get("/{remediation_id}", response_model=RemediationDetailResponse)
async def get_remediation_details(remediation_id: str):
    """
    Get detailed information about a specific remediation
    
    Args:
        remediation_id: Unique remediation ID
        
    Returns:
        Detailed remediation information including approval request, violation details, and analysis
    """
    try:
        skill = get_remediation_skill()
        remediation = skill.get_remediation_by_id(remediation_id)
        
        if not remediation:
            raise HTTPException(status_code=404, detail=f"Remediation not found: {remediation_id}")
        
        return RemediationDetailResponse(
            approval_request=remediation['request'],
            violation_details=remediation['violation_details'],
            analysis_data=remediation['analysis_data'],
            created_at=remediation['created_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting remediation details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get remediation details: {str(e)}")


@router.post("/{remediation_id}/approve", response_model=ApprovalResponse)
async def approve_remediation(
    remediation_id: str,
    decision: ApprovalDecision = Body(...)
):
    """
    Approve or reject a remediation request
    
    Args:
        remediation_id: Unique remediation ID
        decision: Approval decision with action, approver, and optional comments
        
    Returns:
        Approval response with execution details
    """
    try:
        skill = get_remediation_skill()
        remediation = skill.get_remediation_by_id(remediation_id)
        
        if not remediation:
            raise HTTPException(status_code=404, detail=f"Remediation not found: {remediation_id}")
        
        # Validate action
        valid_actions = ['approve_automated', 'approve_manual', 'approve_scheduled', 'reject', 'request_more_info']
        if decision.action not in valid_actions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action. Must be one of: {', '.join(valid_actions)}"
            )
        
        # Check if automation is available for automated approval
        if decision.action == 'approve_automated':
            if not remediation['request']['remediation_details']['automation_available']:
                raise HTTPException(
                    status_code=400,
                    detail="Automated remediation not available for this violation"
                )
        
        # Update remediation status
        success = skill.update_remediation_status(
            remediation_id,
            decision.action,
            decision.approver,
            decision.comments
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update remediation status")
        
        # Prepare response
        response_messages = {
            'approve_automated': 'Remediation approved and will be executed automatically',
            'approve_manual': 'Remediation approved for manual execution',
            'approve_scheduled': f'Remediation approved and scheduled for {decision.scheduled_time}',
            'reject': 'Remediation rejected',
            'request_more_info': 'More information requested'
        }
        
        execution_details = None
        
        # If automated approval, prepare execution details
        if decision.action == 'approve_automated':
            execution_details = {
                'execution_status': 'queued',
                'execution_time': datetime.now(timezone.utc).isoformat(),
                'automated': True,
                'steps': remediation['request']['remediation_details'].get('automated_steps', [])
            }
            
            # In a real implementation, this would trigger the automated remediation
            logger.info(f"Automated remediation queued for execution: {remediation_id}")
        
        elif decision.action == 'approve_scheduled':
            execution_details = {
                'execution_status': 'scheduled',
                'scheduled_time': decision.scheduled_time,
                'automated': False
            }
        
        # Broadcast approval decision via WebSocket
        await _broadcast_approval_decision(remediation_id, decision, remediation)
        
        return ApprovalResponse(
            success=True,
            message=response_messages[decision.action],
            remediation_id=remediation_id,
            status=decision.action,
            execution_details=execution_details
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving remediation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to approve remediation: {str(e)}")


@router.post("/{remediation_id}/execute", response_model=dict)
async def execute_remediation(remediation_id: str):
    """
    Execute an approved remediation (for manual execution trigger)
    
    Args:
        remediation_id: Unique remediation ID
        
    Returns:
        Execution status and details
    """
    try:
        skill = get_remediation_skill()
        remediation = skill.get_remediation_by_id(remediation_id)
        
        if not remediation:
            raise HTTPException(status_code=404, detail=f"Remediation not found: {remediation_id}")
        
        # Check if remediation is approved
        status = remediation['request']['status']
        if status not in ['approve_automated', 'approve_manual', 'approve_scheduled']:
            raise HTTPException(
                status_code=400,
                detail=f"Remediation must be approved before execution. Current status: {status}"
            )
        
        # In a real implementation, this would execute the remediation
        # For now, we'll return a mock execution response
        execution_result = {
            'remediation_id': remediation_id,
            'execution_status': 'in_progress',
            'started_at': datetime.now(timezone.utc).isoformat(),
            'steps_completed': 0,
            'total_steps': len(remediation['request']['remediation_details'].get('automated_steps', [])),
            'message': 'Remediation execution started'
        }
        
        logger.info(f"Remediation execution started: {remediation_id}")
        
        # Broadcast execution status
        await ws_manager.broadcast({
            'type': 'remediation_execution_started',
            'data': execution_result
        })
        
        return execution_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing remediation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to execute remediation: {str(e)}")


@router.get("/{remediation_id}/status", response_model=dict)
async def get_remediation_status(remediation_id: str):
    """
    Get current status of a remediation
    
    Args:
        remediation_id: Unique remediation ID
        
    Returns:
        Current remediation status
    """
    try:
        skill = get_remediation_skill()
        remediation = skill.get_remediation_by_id(remediation_id)
        
        if not remediation:
            raise HTTPException(status_code=404, detail=f"Remediation not found: {remediation_id}")
        
        request = remediation['request']
        
        return {
            'remediation_id': remediation_id,
            'status': request['status'],
            'created_at': request['created_at'],
            'expires_at': request['expires_at'],
            'approved_by': request.get('approved_by'),
            'approved_at': request.get('approved_at'),
            'approver_comments': request.get('approver_comments'),
            'bucket_name': request['violation_summary']['bucket_name'],
            'drift_type': request['violation_summary']['drift_type'],
            'risk_score': request['impact_summary']['risk_score']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting remediation status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get remediation status: {str(e)}")


async def _broadcast_approval_decision(
    remediation_id: str,
    decision: ApprovalDecision,
    remediation: dict
):
    """Broadcast approval decision via WebSocket"""
    try:
        message = {
            'type': 'remediation_approval_decision',
            'data': {
                'remediation_id': remediation_id,
                'action': decision.action,
                'approver': decision.approver,
                'comments': decision.comments,
                'bucket_name': remediation['request']['violation_summary']['bucket_name'],
                'drift_type': remediation['request']['violation_summary']['drift_type'],
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        }
        
        await ws_manager.broadcast(message)
        logger.info(f"Broadcasted approval decision for remediation: {remediation_id}")
        
    except Exception as e:
        logger.error(f"Error broadcasting approval decision: {e}")


# Health check endpoint
@router.get("/health")
async def remediation_health():
    """Health check for remediation service"""
    skill = get_remediation_skill()
    pending = skill.get_pending_remediations()
    
    return {
        'status': 'healthy',
        'service': 'remediation_approval',
        'pending_remediations': len(pending),
        'timestamp': datetime.now(timezone.utc).isoformat()
    }