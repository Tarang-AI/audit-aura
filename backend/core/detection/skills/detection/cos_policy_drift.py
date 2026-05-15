"""
COS Bucket Policy Drift Detection Skill
Detects when COS bucket policies are changed to allow public access
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from ..core.base import Skill, SkillResult, SkillCategory

logger = logging.getLogger(__name__)


class COSPolicyDriftDetectionSkill(Skill):
    """Detects COS bucket policy drift - specifically public access changes"""
    
    skill_id = "detect_cos_policy_drift"
    name = "COS Policy Drift Detection"
    description = "Detects when COS bucket policies are changed to allow public access"
    category = SkillCategory.DETECTION
    required_capabilities = ['policy_analysis', 'drift_detection']
    provider = 'ibm_cloud'
    
    def __init__(self):
        """Initialize COS policy drift detection skill"""
        self.baseline_policies: Dict[str, Dict[str, Any]] = {}
        logger.info("COS Policy Drift Detection Skill initialized")
    
    def is_applicable(self, context: Dict[str, Any]) -> bool:
        """Check if this skill applies to the event"""
        event = context.get('event', {})
        
        # Check for COS-related events
        event_name = event.get('event_name', '').lower()
        resource_type = event.get('resource_type', '').lower()
        
        # Applicable for COS bucket policy changes
        cos_events = [
            'putbucketpolicy',
            'setbucketpolicy', 
            'updatebucketpolicy',
            'modifybucketacl',
            'putbucketacl'
        ]
        
        is_cos_event = any(evt in event_name for evt in cos_events)
        is_cos_resource = 'bucket' in resource_type or 'cos' in resource_type or 's3' in resource_type
        
        return is_cos_event or is_cos_resource
    
    def execute(self, context: Dict[str, Any]) -> SkillResult:
        """Execute COS policy drift detection"""
        event = context.get('event', {})
        
        try:
            # Extract bucket information
            bucket_name = self._extract_bucket_name(event)
            current_policy = self._extract_policy_details(event)
            
            # Check for drift
            drift_detected, drift_details = self._detect_drift(
                bucket_name, 
                current_policy
            )
            
            if drift_detected:
                logger.warning(
                    f"COS Policy Drift Detected: {bucket_name} - "
                    f"{drift_details.get('drift_type', 'Unknown')}"
                )
                
                return SkillResult(
                    success=True,
                    applicable=True,
                    violation_detected=True,
                    severity=self._calculate_severity(drift_details),
                    details={
                        'control_id': 'COS-POLICY-001',
                        'control_description': 'COS bucket policy must not allow public access',
                        'standard': ['SOC2', 'ISO27001', 'GDPR'],
                        'category': 'Data Protection',
                        'bucket_name': bucket_name,
                        'drift_type': drift_details.get('drift_type'),
                        'previous_policy': drift_details.get('previous_policy'),
                        'current_policy': current_policy,
                        'changes_detected': drift_details.get('changes'),
                        'public_access_enabled': current_policy.get('public', False),
                        'event': event,
                        'remediation': self._generate_remediation(bucket_name, drift_details),
                        'skill_id': self.skill_id,
                        'skill_name': self.name,
                        'detected_at': datetime.now(timezone.utc).isoformat()
                    },
                    requires_followup=True,
                    followup_skills=['analyze_security_impact', 'generate_remediation']
                )
            else:
                # No drift detected - policy change is compliant
                return SkillResult(
                    success=True,
                    applicable=True,
                    violation_detected=False,
                    details={
                        'control_id': 'COS-POLICY-001',
                        'status': 'compliant',
                        'bucket_name': bucket_name,
                        'skill_id': self.skill_id,
                        'message': 'Policy change does not introduce security risks'
                    }
                )
        
        except Exception as e:
            logger.error(f"Error in COS policy drift detection: {e}", exc_info=True)
            return SkillResult(
                success=False,
                applicable=True,
                details={
                    'error': str(e),
                    'skill_id': self.skill_id
                }
            )
    
    def _extract_bucket_name(self, event: Dict[str, Any]) -> str:
        """Extract bucket name from event"""
        # Try multiple fields
        bucket_name = (
            event.get('resource_name') or
            event.get('bucket_name') or
            event.get('bucket') or
            event.get('resource', {}).get('name') or
            'unknown-bucket'
        )
        return bucket_name
    
    def _extract_policy_details(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Extract policy details from event"""
        policy = {
            'public': event.get('public', False),
            'encryption_enabled': event.get('encryption_enabled', False),
            'versioning_enabled': event.get('versioning_enabled', False),
            'access_control': event.get('access_control', 'private'),
            'cors_enabled': event.get('cors_enabled', False),
            'lifecycle_rules': event.get('lifecycle_rules', []),
            'timestamp': event.get('event_time', datetime.now(timezone.utc).isoformat())
        }
        
        # Extract from nested policy object if present
        if 'policy' in event:
            policy_obj = event['policy']
            if isinstance(policy_obj, dict):
                policy.update({
                    'public': policy_obj.get('public_access', policy['public']),
                    'statements': policy_obj.get('statements', []),
                    'principals': policy_obj.get('principals', [])
                })
        
        return policy
    
    def _detect_drift(
        self, 
        bucket_name: str, 
        current_policy: Dict[str, Any]
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Detect policy drift by comparing with baseline
        
        Returns:
            Tuple of (drift_detected, drift_details)
        """
        drift_details = {
            'drift_type': None,
            'changes': [],
            'previous_policy': None
        }
        
        # Check if we have a baseline for this bucket
        if bucket_name in self.baseline_policies:
            previous_policy = self.baseline_policies[bucket_name]
            drift_details['previous_policy'] = previous_policy
            
            # Detect changes
            changes = []
            
            # Critical: Public access change
            if previous_policy.get('public') != current_policy.get('public'):
                if current_policy.get('public'):
                    changes.append({
                        'field': 'public_access',
                        'from': False,
                        'to': True,
                        'severity': 'critical',
                        'description': 'Bucket changed from private to public'
                    })
                    drift_details['drift_type'] = 'public_access_enabled'
                else:
                    changes.append({
                        'field': 'public_access',
                        'from': True,
                        'to': False,
                        'severity': 'low',
                        'description': 'Bucket changed from public to private (remediation)'
                    })
            
            # High: Encryption disabled
            if previous_policy.get('encryption_enabled') and not current_policy.get('encryption_enabled'):
                changes.append({
                    'field': 'encryption',
                    'from': True,
                    'to': False,
                    'severity': 'high',
                    'description': 'Encryption disabled on bucket'
                })
                drift_details['drift_type'] = drift_details.get('drift_type') or 'encryption_disabled'
            
            # Medium: Versioning disabled
            if previous_policy.get('versioning_enabled') and not current_policy.get('versioning_enabled'):
                changes.append({
                    'field': 'versioning',
                    'from': True,
                    'to': False,
                    'severity': 'medium',
                    'description': 'Versioning disabled on bucket'
                })
                drift_details['drift_type'] = drift_details.get('drift_type') or 'versioning_disabled'
            
            drift_details['changes'] = changes
            
            # Drift detected if there are any critical or high severity changes
            drift_detected = any(
                change['severity'] in ['critical', 'high'] 
                for change in changes
            )
        else:
            # First time seeing this bucket - check if it's public
            if current_policy.get('public'):
                drift_details['drift_type'] = 'new_public_bucket'
                drift_details['changes'] = [{
                    'field': 'public_access',
                    'from': None,
                    'to': True,
                    'severity': 'critical',
                    'description': 'New bucket created with public access'
                }]
                drift_detected = True
            else:
                drift_detected = False
        
        # Update baseline with current policy
        self.baseline_policies[bucket_name] = current_policy.copy()
        
        return drift_detected, drift_details
    
    def _calculate_severity(self, drift_details: Dict[str, Any]) -> str:
        """Calculate overall severity based on drift details"""
        changes = drift_details.get('changes', [])
        
        if not changes:
            return 'low'
        
        # Get highest severity from changes
        severity_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        max_severity = max(
            (severity_order.get(change.get('severity', 'low'), 1) for change in changes),
            default=1
        )
        
        for severity, value in severity_order.items():
            if value == max_severity:
                return severity
        
        return 'medium'
    
    def _generate_remediation(
        self, 
        bucket_name: str, 
        drift_details: Dict[str, Any]
    ) -> str:
        """Generate remediation steps based on drift type"""
        drift_type = drift_details.get('drift_type', 'unknown')
        
        remediation_templates = {
            'public_access_enabled': f"""
IMMEDIATE ACTION REQUIRED:
1. Navigate to IBM Cloud Object Storage console
2. Select bucket: {bucket_name}
3. Go to Access Policies section
4. Remove public access permissions
5. Set bucket ACL to private
6. Verify no public read/write permissions exist
7. Enable bucket access logging for audit trail
8. Review and update IAM policies to prevent unauthorized changes
            """.strip(),
            
            'encryption_disabled': f"""
ACTION REQUIRED:
1. Navigate to IBM Cloud Object Storage console
2. Select bucket: {bucket_name}
3. Go to Configuration section
4. Enable server-side encryption (SSE)
5. Select appropriate encryption key (IBM-managed or customer-managed)
6. Verify encryption is active
7. Update bucket policy to enforce encryption
            """.strip(),
            
            'versioning_disabled': f"""
ACTION RECOMMENDED:
1. Navigate to IBM Cloud Object Storage console
2. Select bucket: {bucket_name}
3. Go to Configuration section
4. Enable versioning
5. Configure lifecycle policies for version management
6. Verify versioning is active
            """.strip(),
            
            'new_public_bucket': f"""
IMMEDIATE ACTION REQUIRED:
1. Review business justification for public bucket
2. If public access not required:
   - Navigate to IBM Cloud Object Storage console
   - Select bucket: {bucket_name}
   - Set bucket ACL to private
   - Remove all public access permissions
3. If public access is required:
   - Document business justification
   - Implement least-privilege access controls
   - Enable access logging
   - Set up monitoring alerts
   - Get security team approval
            """.strip()
        }
        
        return remediation_templates.get(
            drift_type,
            f"Review and remediate policy changes for bucket: {bucket_name}"
        )
    
    def get_baseline_policies(self) -> Dict[str, Dict[str, Any]]:
        """Get current baseline policies for all buckets"""
        return self.baseline_policies.copy()
    
    def set_baseline_policy(self, bucket_name: str, policy: Dict[str, Any]):
        """Manually set baseline policy for a bucket"""
        self.baseline_policies[bucket_name] = policy.copy()
        logger.info(f"Baseline policy set for bucket: {bucket_name}")
    
    def clear_baseline(self, bucket_name: Optional[str] = None):
        """Clear baseline policies"""
        if bucket_name:
            if bucket_name in self.baseline_policies:
                del self.baseline_policies[bucket_name]
                logger.info(f"Baseline cleared for bucket: {bucket_name}")
        else:
            self.baseline_policies.clear()
            logger.info("All baseline policies cleared")