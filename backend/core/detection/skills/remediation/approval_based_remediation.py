"""
Approval-Based Remediation Skill
Generates remediation plans that require admin approval before execution
"""
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from ..core.base import Skill, SkillResult, SkillCategory

logger = logging.getLogger(__name__)


class ApprovalBasedRemediationSkill(Skill):
    """Generates remediation plans requiring admin approval"""
    
    skill_id = "generate_remediation_with_approval"
    name = "Approval-Based Remediation Generation"
    description = "Generates detailed remediation plans requiring admin approval before execution"
    category = SkillCategory.REMEDIATION
    required_capabilities = ['remediation_planning', 'approval_workflow']
    provider = 'all'
    
    def __init__(self):
        """Initialize approval-based remediation skill"""
        self.pending_remediations: Dict[str, Dict[str, Any]] = {}
        logger.info("Approval-Based Remediation Skill initialized")
    
    def is_applicable(self, context: Dict[str, Any]) -> bool:
        """Check if remediation is needed"""
        previous_result = context.get('previous_result', {})
        return previous_result.get('violation_detected', False)
    
    def execute(self, context: Dict[str, Any]) -> SkillResult:
        """Generate approval-based remediation plan"""
        previous_result = context.get('previous_result', {})
        violation_details = previous_result.get('details', {})
        analysis_results = context.get('analysis', [])
        
        # Extract key information
        control_id = violation_details.get('control_id')
        bucket_name = violation_details.get('bucket_name', 'unknown')
        drift_type = violation_details.get('drift_type', 'unknown')
        
        # Get analysis data - ensure it's a dictionary
        analysis_data = {}
        if analysis_results:
            first_result = analysis_results[0]
            # Handle both dict and string cases
            if isinstance(first_result, dict):
                analysis_data = first_result
            elif isinstance(first_result, str):
                logger.warning(f"Analysis result is a string, not a dict: {first_result[:100]}")
                analysis_data = {}
            else:
                logger.warning(f"Unexpected analysis result type: {type(first_result)}")
                analysis_data = {}
        
        # Safe extraction with type checking
        risk_score = analysis_data.get('risk_score', 5) if isinstance(analysis_data, dict) else 5
        security_impact = analysis_data.get('security_impact', {}) if isinstance(analysis_data, dict) else {}
        compliance_impact = analysis_data.get('compliance_impact', {}) if isinstance(analysis_data, dict) else {}
        
        # Generate remediation plan
        remediation_plan = self._generate_comprehensive_plan(
            violation_details,
            analysis_data,
            risk_score
        )
        
        # Create approval request
        approval_request = self._create_approval_request(
            violation_details,
            remediation_plan,
            analysis_data
        )
        
        # Store pending remediation
        self.pending_remediations[approval_request['id']] = {
            'request': approval_request,
            'violation_details': violation_details,
            'analysis_data': analysis_data,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(
            f"Remediation plan generated for {bucket_name} - "
            f"Approval ID: {approval_request['id']}"
        )
        
        return SkillResult(
            success=True,
            applicable=True,
            details={
                'skill_id': self.skill_id,
                'skill_name': self.name,
                'approval_request': approval_request,
                'remediation_plan': remediation_plan,
                'requires_approval': True,
                'approval_deadline': self._calculate_approval_deadline(risk_score),
                'escalation_required': risk_score >= 8
            },
            requires_followup=True,
            followup_skills=['notify_admin_for_approval']
        )
    
    def _generate_comprehensive_plan(
        self,
        violation_details: Dict[str, Any],
        analysis_data: Dict[str, Any],
        risk_score: int
    ) -> Dict[str, Any]:
        """Generate comprehensive remediation plan"""
        bucket_name = violation_details.get('bucket_name', 'unknown')
        drift_type = violation_details.get('drift_type', 'unknown')
        current_policy = violation_details.get('current_policy', {})
        
        # Safe extraction of priority
        recommended_priority = 'P2 - Medium'
        if isinstance(analysis_data, dict):
            recommended_priority = analysis_data.get('recommended_priority', 'P2 - Medium')
        
        plan = {
            'plan_id': str(uuid.uuid4()),
            'bucket_name': bucket_name,
            'drift_type': drift_type,
            'risk_score': risk_score,
            'priority': recommended_priority,
            'estimated_time': self._estimate_remediation_time(drift_type, risk_score),
            'automation_available': self._check_automation_capability(drift_type),
            'manual_steps': self._generate_manual_steps(violation_details, drift_type),
            'automated_steps': self._generate_automated_steps(violation_details, drift_type),
            'verification_steps': self._generate_verification_steps(drift_type),
            'rollback_plan': self._generate_rollback_plan(drift_type, current_policy),
            'prerequisites': self._identify_prerequisites(drift_type),
            'risks_of_remediation': self._assess_remediation_risks(drift_type),
            'success_criteria': self._define_success_criteria(drift_type),
            'post_remediation_actions': self._define_post_remediation_actions(drift_type)
        }
        
        return plan
    
    def _create_approval_request(
        self,
        violation_details: Dict[str, Any],
        remediation_plan: Dict[str, Any],
        analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create approval request for admin"""
        approval_id = str(uuid.uuid4())
        bucket_name = violation_details.get('bucket_name', 'unknown')
        drift_type = violation_details.get('drift_type', 'unknown')
        risk_score = analysis_data.get('risk_score', 5)
        
        # Safe extraction helpers
        def safe_get_nested(data: Any, key: str, nested_key: Optional[str] = None, default: Any = None) -> Any:
            """Safely get nested dictionary values"""
            value = data.get(key, {}) if isinstance(data, dict) else {}
            if nested_key and isinstance(value, dict):
                return value.get(nested_key, default)
            elif nested_key:
                return default
            return value if isinstance(value, dict) else default or {}
        
        def safe_get_value(data: Any, key: str, default: Any = None) -> Any:
            """Safely get value from dict or return default"""
            if isinstance(data, dict):
                return data.get(key, default)
            return default
        
        # Extract security impact
        security_impact = safe_get_nested(analysis_data, 'security_impact')
        compliance_impact = safe_get_nested(analysis_data, 'compliance_impact')
        data_exposure_risk = safe_get_nested(analysis_data, 'data_exposure_risk')
        blast_radius = safe_get_nested(analysis_data, 'blast_radius')
        
        request = {
            'id': approval_id,
            'type': 'remediation_approval',
            'status': 'pending',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'expires_at': self._calculate_approval_deadline(risk_score),
            
            # Violation summary
            'violation_summary': {
                'control_id': violation_details.get('control_id'),
                'bucket_name': bucket_name,
                'drift_type': drift_type,
                'detected_at': violation_details.get('detected_at'),
                'severity': violation_details.get('severity', 'medium')
            },
            
            # Impact summary
            'impact_summary': {
                'risk_score': risk_score,
                'priority': safe_get_value(analysis_data, 'recommended_priority'),
                'security_impact_level': safe_get_value(security_impact, 'level') if isinstance(security_impact, dict) else None,
                'compliance_frameworks_affected': safe_get_value(compliance_impact, 'frameworks_affected', []) if isinstance(compliance_impact, dict) else [],
                'data_exposure_risk': safe_get_value(data_exposure_risk, 'level') if isinstance(data_exposure_risk, dict) else None,
                'blast_radius': safe_get_value(blast_radius, 'scope') if isinstance(blast_radius, dict) else blast_radius,
                'incident_classification': safe_get_value(analysis_data, 'incident_classification')
            },
            
            # Remediation details
            'remediation_details': {
                'plan_id': remediation_plan['plan_id'],
                'estimated_time': remediation_plan['estimated_time'],
                'automation_available': remediation_plan['automation_available'],
                'requires_downtime': False,
                'reversible': True
            },
            
            # Approval options
            'approval_options': [
                {
                    'action': 'approve_automated',
                    'label': 'Approve & Execute Automatically',
                    'description': 'Approve and execute automated remediation immediately',
                    'available': remediation_plan['automation_available'],
                    'recommended': risk_score >= 8 and remediation_plan['automation_available']
                },
                {
                    'action': 'approve_manual',
                    'label': 'Approve for Manual Execution',
                    'description': 'Approve remediation plan for manual execution by ops team',
                    'available': True,
                    'recommended': not remediation_plan['automation_available']
                },
                {
                    'action': 'approve_scheduled',
                    'label': 'Approve & Schedule',
                    'description': 'Approve and schedule remediation for specific time',
                    'available': True,
                    'recommended': risk_score < 8
                },
                {
                    'action': 'reject',
                    'label': 'Reject',
                    'description': 'Reject remediation (requires justification)',
                    'available': True,
                    'recommended': False
                },
                {
                    'action': 'request_more_info',
                    'label': 'Request More Information',
                    'description': 'Request additional analysis before decision',
                    'available': True,
                    'recommended': False
                }
            ],
            
            # Required approvers
            'required_approvers': self._identify_required_approvers(risk_score, drift_type),
            
            # Notification recipients
            'notification_recipients': safe_get_value(analysis_data, 'affected_stakeholders', []),
            
            # Additional context
            'additional_context': {
                'regulatory_implications': safe_get_nested(analysis_data, 'regulatory_implications'),
                'business_impact': safe_get_nested(analysis_data, 'business_impact'),
                'attack_vectors': safe_get_value(security_impact, 'attack_vectors', []) if isinstance(security_impact, dict) else []
            }
        }
        
        return request
    
    def _generate_manual_steps(
        self,
        violation_details: Dict[str, Any],
        drift_type: str
    ) -> List[Dict[str, Any]]:
        """Generate detailed manual remediation steps"""
        bucket_name = violation_details.get('bucket_name', 'unknown')
        
        steps_templates = {
            'public_access_enabled': [
                {
                    'step': 1,
                    'action': 'Access IBM Cloud Console',
                    'description': 'Log in to IBM Cloud console with admin credentials',
                    'estimated_time': '1 minute',
                    'verification': 'Confirm successful login'
                },
                {
                    'step': 2,
                    'action': 'Navigate to Object Storage',
                    'description': f'Go to Object Storage service and locate bucket: {bucket_name}',
                    'estimated_time': '2 minutes',
                    'verification': 'Bucket is visible in console'
                },
                {
                    'step': 3,
                    'action': 'Review Current Policy',
                    'description': 'Document current bucket policy and access settings',
                    'estimated_time': '3 minutes',
                    'verification': 'Policy documented for audit trail'
                },
                {
                    'step': 4,
                    'action': 'Remove Public Access',
                    'description': 'Navigate to Access Policies → Remove all public access permissions',
                    'estimated_time': '5 minutes',
                    'verification': 'No public access permissions remain',
                    'critical': True
                },
                {
                    'step': 5,
                    'action': 'Set Bucket ACL to Private',
                    'description': 'Change bucket ACL from public-read to private',
                    'estimated_time': '2 minutes',
                    'verification': 'ACL shows as private',
                    'critical': True
                },
                {
                    'step': 6,
                    'action': 'Enable Access Logging',
                    'description': 'Enable bucket access logging for audit trail',
                    'estimated_time': '3 minutes',
                    'verification': 'Logging enabled and configured'
                },
                {
                    'step': 7,
                    'action': 'Update IAM Policies',
                    'description': 'Review and update IAM policies to prevent unauthorized changes',
                    'estimated_time': '10 minutes',
                    'verification': 'IAM policies restrict bucket policy modifications'
                },
                {
                    'step': 8,
                    'action': 'Test Access',
                    'description': 'Verify bucket is not publicly accessible',
                    'estimated_time': '5 minutes',
                    'verification': 'Public access test fails (expected)',
                    'critical': True
                },
                {
                    'step': 9,
                    'action': 'Document Changes',
                    'description': 'Document all changes in change management system',
                    'estimated_time': '5 minutes',
                    'verification': 'Change ticket updated'
                }
            ],
            'encryption_disabled': [
                {
                    'step': 1,
                    'action': 'Access IBM Cloud Console',
                    'description': 'Log in to IBM Cloud console',
                    'estimated_time': '1 minute',
                    'verification': 'Successful login'
                },
                {
                    'step': 2,
                    'action': 'Navigate to Bucket',
                    'description': f'Locate bucket: {bucket_name}',
                    'estimated_time': '2 minutes',
                    'verification': 'Bucket located'
                },
                {
                    'step': 3,
                    'action': 'Enable Encryption',
                    'description': 'Go to Configuration → Enable server-side encryption',
                    'estimated_time': '5 minutes',
                    'verification': 'Encryption enabled',
                    'critical': True
                },
                {
                    'step': 4,
                    'action': 'Select Encryption Key',
                    'description': 'Choose IBM-managed or customer-managed key',
                    'estimated_time': '3 minutes',
                    'verification': 'Key selected and configured'
                },
                {
                    'step': 5,
                    'action': 'Verify Encryption',
                    'description': 'Confirm encryption is active for new objects',
                    'estimated_time': '5 minutes',
                    'verification': 'New objects are encrypted',
                    'critical': True
                }
            ],
            'versioning_disabled': [
                {
                    'step': 1,
                    'action': 'Access Bucket Configuration',
                    'description': f'Navigate to bucket {bucket_name} configuration',
                    'estimated_time': '2 minutes',
                    'verification': 'Configuration page loaded'
                },
                {
                    'step': 2,
                    'action': 'Enable Versioning',
                    'description': 'Enable object versioning',
                    'estimated_time': '3 minutes',
                    'verification': 'Versioning enabled',
                    'critical': True
                },
                {
                    'step': 3,
                    'action': 'Configure Lifecycle',
                    'description': 'Set up lifecycle policies for version management',
                    'estimated_time': '10 minutes',
                    'verification': 'Lifecycle policies configured'
                }
            ]
        }
        
        return steps_templates.get(drift_type, [])
    
    def _generate_automated_steps(
        self,
        violation_details: Dict[str, Any],
        drift_type: str
    ) -> List[Dict[str, Any]]:
        """Generate automated remediation steps"""
        bucket_name = violation_details.get('bucket_name', 'unknown')
        
        automated_steps = {
            'public_access_enabled': [
                {
                    'step': 1,
                    'action': 'remove_public_access',
                    'description': f'Remove public access from bucket {bucket_name}',
                    'api_call': 'ibm_cos.set_bucket_acl(Bucket=bucket_name, ACL="private")',
                    'estimated_time': '10 seconds',
                    'reversible': True
                },
                {
                    'step': 2,
                    'action': 'update_bucket_policy',
                    'description': 'Update bucket policy to deny public access',
                    'api_call': 'ibm_cos.put_bucket_policy(Bucket=bucket_name, Policy=private_policy)',
                    'estimated_time': '5 seconds',
                    'reversible': True
                },
                {
                    'step': 3,
                    'action': 'enable_logging',
                    'description': 'Enable access logging',
                    'api_call': 'ibm_cos.put_bucket_logging(Bucket=bucket_name, BucketLoggingStatus=logging_config)',
                    'estimated_time': '5 seconds',
                    'reversible': True
                },
                {
                    'step': 4,
                    'action': 'verify_remediation',
                    'description': 'Verify bucket is no longer public',
                    'api_call': 'ibm_cos.get_bucket_acl(Bucket=bucket_name)',
                    'estimated_time': '5 seconds',
                    'reversible': False
                }
            ],
            'encryption_disabled': [
                {
                    'step': 1,
                    'action': 'enable_encryption',
                    'description': f'Enable encryption on bucket {bucket_name}',
                    'api_call': 'ibm_cos.put_bucket_encryption(Bucket=bucket_name, ServerSideEncryptionConfiguration=encryption_config)',
                    'estimated_time': '10 seconds',
                    'reversible': True
                },
                {
                    'step': 2,
                    'action': 'verify_encryption',
                    'description': 'Verify encryption is enabled',
                    'api_call': 'ibm_cos.get_bucket_encryption(Bucket=bucket_name)',
                    'estimated_time': '5 seconds',
                    'reversible': False
                }
            ],
            'versioning_disabled': [
                {
                    'step': 1,
                    'action': 'enable_versioning',
                    'description': f'Enable versioning on bucket {bucket_name}',
                    'api_call': 'ibm_cos.put_bucket_versioning(Bucket=bucket_name, VersioningConfiguration={"Status": "Enabled"})',
                    'estimated_time': '10 seconds',
                    'reversible': True
                }
            ]
        }
        
        return automated_steps.get(drift_type, [])
    
    def _generate_verification_steps(self, drift_type: str) -> List[str]:
        """Generate verification steps"""
        verification_templates = {
            'public_access_enabled': [
                'Attempt to access bucket without authentication (should fail)',
                'Verify bucket ACL shows "private"',
                'Check bucket policy has no public access statements',
                'Confirm access logging is enabled',
                'Run compliance check to verify control passes',
                'Test authorized access still works'
            ],
            'encryption_disabled': [
                'Verify encryption configuration is enabled',
                'Upload test object and verify it is encrypted',
                'Check encryption key is properly configured',
                'Run compliance check to verify control passes'
            ],
            'versioning_disabled': [
                'Verify versioning status is "Enabled"',
                'Upload test object and verify version is created',
                'Check lifecycle policies are configured',
                'Run compliance check to verify control passes'
            ]
        }
        
        return verification_templates.get(drift_type, ['Verify remediation was successful'])
    
    def _generate_rollback_plan(
        self,
        drift_type: str,
        current_policy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate rollback plan in case remediation causes issues"""
        return {
            'available': True,
            'description': 'Rollback to previous policy configuration',
            'steps': [
                'Stop remediation process',
                'Restore previous bucket policy from backup',
                'Verify services are functioning',
                'Document rollback reason',
                'Escalate to senior team'
            ],
            'previous_policy': current_policy,
            'estimated_rollback_time': '5-10 minutes'
        }
    
    def _identify_prerequisites(self, drift_type: str) -> List[str]:
        """Identify prerequisites for remediation"""
        common_prerequisites = [
            'Admin access to IBM Cloud console',
            'Appropriate IAM permissions',
            'Change management approval',
            'Backup of current configuration'
        ]
        
        specific_prerequisites = {
            'public_access_enabled': [
                'Verify no legitimate public access requirements',
                'Notify application teams of access change',
                'Prepare alternative access methods if needed'
            ],
            'encryption_disabled': [
                'Select encryption key (IBM-managed or customer-managed)',
                'Verify key management service is available',
                'Plan for re-encryption of existing objects if needed'
            ],
            'versioning_disabled': [
                'Assess storage cost impact',
                'Define version retention policy',
                'Configure lifecycle rules'
            ]
        }
        
        return common_prerequisites + specific_prerequisites.get(drift_type, [])
    
    def _assess_remediation_risks(self, drift_type: str) -> List[Dict[str, str]]:
        """Assess risks of performing remediation"""
        risks = {
            'public_access_enabled': [
                {
                    'risk': 'Service disruption',
                    'likelihood': 'Low',
                    'impact': 'Medium',
                    'mitigation': 'Verify no applications depend on public access before remediation'
                },
                {
                    'risk': 'Broken integrations',
                    'likelihood': 'Low',
                    'impact': 'Medium',
                    'mitigation': 'Test authorized access after remediation'
                }
            ],
            'encryption_disabled': [
                {
                    'risk': 'Performance impact',
                    'likelihood': 'Low',
                    'impact': 'Low',
                    'mitigation': 'Encryption overhead is minimal with modern systems'
                },
                {
                    'risk': 'Key management complexity',
                    'likelihood': 'Medium',
                    'impact': 'Low',
                    'mitigation': 'Use IBM-managed keys for simplicity'
                }
            ],
            'versioning_disabled': [
                {
                    'risk': 'Increased storage costs',
                    'likelihood': 'High',
                    'impact': 'Low-Medium',
                    'mitigation': 'Configure lifecycle policies to manage versions'
                }
            ]
        }
        
        return risks.get(drift_type, [])
    
    def _define_success_criteria(self, drift_type: str) -> List[str]:
        """Define success criteria for remediation"""
        criteria_templates = {
            'public_access_enabled': [
                'Bucket is no longer publicly accessible',
                'Bucket ACL is set to private',
                'No public access statements in bucket policy',
                'Access logging is enabled',
                'Compliance check passes',
                'Authorized users can still access bucket'
            ],
            'encryption_disabled': [
                'Encryption is enabled on bucket',
                'New objects are encrypted',
                'Encryption key is properly configured',
                'Compliance check passes'
            ],
            'versioning_disabled': [
                'Versioning is enabled',
                'New object versions are created',
                'Lifecycle policies are configured',
                'Compliance check passes'
            ]
        }
        
        return criteria_templates.get(drift_type, ['Remediation completed successfully'])
    
    def _define_post_remediation_actions(self, drift_type: str) -> List[str]:
        """Define actions to take after remediation"""
        return [
            'Update change management ticket',
            'Notify affected stakeholders',
            'Run full compliance scan',
            'Update documentation',
            'Review IAM policies to prevent recurrence',
            'Schedule follow-up review in 7 days',
            'Update incident response playbook if needed'
        ]
    
    def _estimate_remediation_time(self, drift_type: str, risk_score: int) -> str:
        """Estimate time required for remediation"""
        time_estimates = {
            'public_access_enabled': '15-30 minutes (manual) or 1-2 minutes (automated)',
            'encryption_disabled': '10-20 minutes (manual) or 1 minute (automated)',
            'versioning_disabled': '15-25 minutes (manual) or 1 minute (automated)',
            'new_public_bucket': '15-30 minutes (manual) or 1-2 minutes (automated)'
        }
        
        return time_estimates.get(drift_type, '20-40 minutes')
    
    def _check_automation_capability(self, drift_type: str) -> bool:
        """Check if automated remediation is available"""
        # All COS policy drifts can be automated
        return drift_type in [
            'public_access_enabled',
            'encryption_disabled',
            'versioning_disabled',
            'new_public_bucket'
        ]
    
    def _calculate_approval_deadline(self, risk_score: int) -> str:
        """Calculate approval deadline based on risk score"""
        from datetime import timedelta
        
        if risk_score >= 9:
            deadline = datetime.now(timezone.utc) + timedelta(hours=1)
        elif risk_score >= 7:
            deadline = datetime.now(timezone.utc) + timedelta(hours=4)
        elif risk_score >= 5:
            deadline = datetime.now(timezone.utc) + timedelta(hours=24)
        else:
            deadline = datetime.now(timezone.utc) + timedelta(days=7)
        
        return deadline.isoformat()
    
    def _identify_required_approvers(self, risk_score: int, drift_type: str) -> List[Dict[str, str]]:
        """Identify required approvers based on risk"""
        approvers = [
            {
                'role': 'Security Team Lead',
                'required': True,
                'reason': 'Security policy change'
            }
        ]
        
        if risk_score >= 8:
            approvers.extend([
                {
                    'role': 'CISO',
                    'required': True,
                    'reason': 'Critical security incident'
                },
                {
                    'role': 'Compliance Officer',
                    'required': True,
                    'reason': 'Regulatory implications'
                }
            ])
        elif risk_score >= 6:
            approvers.append({
                'role': 'Cloud Infrastructure Manager',
                'required': True,
                'reason': 'Infrastructure change'
            })
        
        return approvers
    
    def get_pending_remediations(self) -> Dict[str, Dict[str, Any]]:
        """Get all pending remediation requests"""
        return self.pending_remediations.copy()
    
    def get_remediation_by_id(self, approval_id: str) -> Optional[Dict[str, Any]]:
        """Get specific remediation request by ID"""
        return self.pending_remediations.get(approval_id)
    
    def update_remediation_status(
        self,
        approval_id: str,
        status: str,
        approver: str,
        comments: Optional[str] = None
    ) -> bool:
        """Update remediation approval status"""
        if approval_id in self.pending_remediations:
            remediation = self.pending_remediations[approval_id]
            remediation['request']['status'] = status
            remediation['request']['approved_by'] = approver
            remediation['request']['approved_at'] = datetime.now(timezone.utc).isoformat()
            remediation['request']['approver_comments'] = comments
            
            logger.info(
                f"Remediation {approval_id} status updated to {status} by {approver}"
            )
            return True
        
        return False