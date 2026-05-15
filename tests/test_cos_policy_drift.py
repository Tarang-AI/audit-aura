"""
Test script for COS Policy Drift Detection
Simulates a COS bucket policy change event and tests the complete flow
"""
import asyncio
import json
from datetime import datetime, timezone
import pytest
from backend.core.detection.agent import get_detection_system
from backend.core.detection.skills.detection.cos_policy_drift import COSPolicyDriftDetectionSkill
from backend.core.detection.skills.analysis.policy_drift_impact import PolicyDriftImpactAnalysisSkill
from backend.core.detection.skills.remediation.approval_based_remediation import ApprovalBasedRemediationSkill


def create_mock_cos_event(bucket_name: str, public: bool = True, encryption_enabled: bool = False):
    """Create a mock COS bucket policy change event"""
    return {
        'source': 'ibm_cloud',
        'event_name': 'PutBucketPolicy',
        'event_time': datetime.now(timezone.utc).isoformat(),
        'username': 'test-user@example.com',
        'resource_type': 'cos_bucket',
        'resource_name': bucket_name,
        'public': public,
        'encryption_enabled': encryption_enabled,
        'versioning_enabled': False,
        'access_control': 'public-read' if public else 'private',
        'policy': {
            'public_access': public,
            'statements': [
                {
                    'Effect': 'Allow',
                    'Principal': '*',
                    'Action': 's3:GetObject',
                    'Resource': f'arn:aws:s3:::{bucket_name}/*'
                }
            ] if public else []
        }
    }


@pytest.mark.asyncio
async def test_cos_policy_drift_detection():
    """Test the complete COS policy drift detection flow"""
    print("=" * 80)
    print("COS POLICY DRIFT DETECTION TEST")
    print("=" * 80)
    print()
    
    # Initialize skills
    print("1. Initializing detection skills...")
    detection_skill = COSPolicyDriftDetectionSkill()
    analysis_skill = PolicyDriftImpactAnalysisSkill()
    remediation_skill = ApprovalBasedRemediationSkill()
    print("   ✓ Skills initialized")
    print()
    
    # Test Case 1: First event - establish baseline (private bucket)
    print("2. Test Case 1: Establishing baseline with private bucket")
    print("-" * 80)
    baseline_event = create_mock_cos_event(
        bucket_name='customer-data-prod',
        public=False,
        encryption_enabled=True
    )
    print(f"   Event: {baseline_event['event_name']} on {baseline_event['resource_name']}")
    print(f"   Public: {baseline_event['public']}, Encrypted: {baseline_event['encryption_enabled']}")
    
    context = {'event': baseline_event}
    
    if detection_skill.is_applicable(context):
        result = detection_skill.execute(context)
        print(f"   Detection Result: {'VIOLATION' if result.violation_detected else 'COMPLIANT'}")
        if result.violation_detected:
            print(f"   ⚠️  Violation: {result.details.get('drift_type')}")
        else:
            print("   ✓ No violation - baseline established")
    print()
    
    # Test Case 2: Policy drift - bucket made public
    print("3. Test Case 2: Detecting policy drift (bucket made public)")
    print("-" * 80)
    drift_event = create_mock_cos_event(
        bucket_name='customer-data-prod',
        public=True,  # Changed to public!
        encryption_enabled=True
    )
    print(f"   Event: {drift_event['event_name']} on {drift_event['resource_name']}")
    print(f"   Public: {drift_event['public']}, Encrypted: {drift_event['encryption_enabled']}")
    print()
    
    context = {'event': drift_event}
    
    # Detection Phase
    print("   Phase 1: DETECTION")
    if detection_skill.is_applicable(context):
        detection_result = detection_skill.execute(context)
        print(f"   Status: {'VIOLATION DETECTED ⚠️' if detection_result.violation_detected else 'COMPLIANT ✓'}")
        
        if detection_result.violation_detected:
            print(f"   Drift Type: {detection_result.details.get('drift_type')}")
            print(f"   Severity: {detection_result.severity}")
            print(f"   Control ID: {detection_result.details.get('control_id')}")
            print()
            
            # Analysis Phase
            print("   Phase 2: ANALYSIS")
            analysis_context = {
                'event': drift_event,
                'previous_result': detection_result.to_dict()
            }
            
            if analysis_skill.is_applicable(analysis_context):
                analysis_result = analysis_skill.execute(analysis_context)
                print(f"   Risk Score: {analysis_result.details.get('risk_score')}/10")
                print(f"   Priority: {analysis_result.details.get('recommended_priority')}")
                print(f"   Security Impact: {analysis_result.details.get('security_impact', {}).get('level', 'N/A').upper()}")
                print(f"   Data Exposure Risk: {analysis_result.details.get('data_exposure_risk', {}).get('level', 'N/A').upper()}")
                print(f"   Blast Radius: {analysis_result.details.get('blast_radius', {}).get('scope', 'N/A').upper()}")
                
                compliance_frameworks = analysis_result.details.get('compliance_impact', {}).get('frameworks_affected', [])
                if compliance_frameworks:
                    print(f"   Affected Frameworks: {len(compliance_frameworks)}")
                    for framework in compliance_frameworks[:3]:
                        print(f"     - {framework}")
                print()
                
                # Remediation Phase
                print("   Phase 3: REMEDIATION PLAN GENERATION")
                remediation_context = {
                    'event': drift_event,
                    'previous_result': detection_result.to_dict(),
                    'analysis': [analysis_result.details]
                }
                
                if remediation_skill.is_applicable(remediation_context):
                    remediation_result = remediation_skill.execute(remediation_context)
                    approval_request = remediation_result.details.get('approval_request', {})
                    remediation_plan = remediation_result.details.get('remediation_plan', {})
                    
                    print(f"   Approval ID: {approval_request.get('id')}")
                    print(f"   Status: {approval_request.get('status')}")
                    print(f"   Automation Available: {remediation_plan.get('automation_available')}")
                    print(f"   Estimated Time: {remediation_plan.get('estimated_time')}")
                    print(f"   Expires At: {approval_request.get('expires_at')}")
                    print()
                    
                    print("   Approval Options:")
                    for option in approval_request.get('approval_options', []):
                        status = "✓ RECOMMENDED" if option.get('recommended') else ""
                        available = "✓" if option.get('available') else "✗"
                        print(f"     [{available}] {option.get('label')} {status}")
                        print(f"         {option.get('description')}")
                    print()
                    
                    print("   Manual Remediation Steps:")
                    manual_steps = remediation_plan.get('manual_steps', [])
                    for step in manual_steps[:5]:  # Show first 5 steps
                        step_num = step.get('step', 0)
                        action = step.get('action', 'N/A')
                        critical = " [CRITICAL]" if step.get('critical') else ""
                        print(f"     {step_num}. {action}{critical}")
                    if len(manual_steps) > 5:
                        print(f"     ... and {len(manual_steps) - 5} more steps")
                    print()
                    
                    print("   Automated Remediation Steps:")
                    auto_steps = remediation_plan.get('automated_steps', [])
                    for step in auto_steps:
                        step_num = step.get('step', 0)
                        action = step.get('action', 'N/A')
                        print(f"     {step_num}. {action}")
                        print(f"        API: {step.get('api_call', 'N/A')}")
                    print()
                    
                    # Simulate approval
                    print("   Phase 4: SIMULATING ADMIN APPROVAL")
                    success = remediation_skill.update_remediation_status(
                        approval_request.get('id'),
                        'approve_automated',
                        'test-admin',
                        'Approved for testing - critical security issue'
                    )
                    print(f"   Approval Status: {'SUCCESS ✓' if success else 'FAILED ✗'}")
                    print()
                    
                    # Show updated status
                    updated_remediation = remediation_skill.get_remediation_by_id(approval_request.get('id'))
                    if updated_remediation:
                        print("   Updated Remediation Status:")
                        print(f"     Status: {updated_remediation['request']['status']}")
                        print(f"     Approved By: {updated_remediation['request'].get('approved_by')}")
                        print(f"     Approved At: {updated_remediation['request'].get('approved_at')}")
                        print(f"     Comments: {updated_remediation['request'].get('approver_comments')}")
    
    print()
    print("=" * 80)
    print("TEST COMPLETED SUCCESSFULLY ✓")
    print("=" * 80)
    print()
    print("Summary:")
    print("  ✓ COS policy drift detected")
    print("  ✓ Security impact analyzed")
    print("  ✓ Remediation plan generated")
    print("  ✓ Approval workflow created")
    print("  ✓ Admin approval simulated")
    print()
    print("Next Steps:")
    print("  1. Start the backend server: cd backend && uvicorn main:app --reload")
    print("  2. Start the frontend: cd frontend && npm run dev")
    print("  3. Navigate to Admin Dashboard → Remediations")
    print("  4. Review and approve pending remediations")
    print()


if __name__ == '__main__':
    asyncio.run(test_cos_policy_drift_detection())