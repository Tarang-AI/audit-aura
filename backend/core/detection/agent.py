"""
Skill-Based Detection Agent
Monitors cloud connections and detects control breaches using skills
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from core.detection.skills.core.base import (
    Skill,
    SkillResult,
    SkillCategory,
    SkillBasedAgent,
)
from core.detection.skills.core.registry import SkillRegistry, get_skill_registry
from core.detection.skills.detection.control_based import (
    ControlBasedDetectionSkill,
    create_detection_skills_from_controls,
)
from core.detection.skills.analysis.security_impact import SecurityImpactAnalysisSkill
from core.detection.skills.analysis.policy_drift_impact import PolicyDriftImpactAnalysisSkill
from core.detection.skills.remediation.plan_generator import RemediationGenerationSkill
from core.detection.skills.remediation.approval_based_remediation import ApprovalBasedRemediationSkill
from core.detection.skills.detection.cos_policy_drift import COSPolicyDriftDetectionSkill
from core.compliance.tracker import get_tracker
from infrastructure.messaging.websocket import ws_manager
from infrastructure.database.vector_store import get_vector_store
from models.skill import SkillMetadata, get_skill_persistence

logger = logging.getLogger(__name__)


class SkillBasedDetectionSystem:
    """
    Skill-based detection system that monitors events and detects violations
    """
    
    def __init__(self):
        self.skill_registry: Optional[SkillRegistry] = None
        self.detection_agent: Optional[SkillBasedAgent] = None
        self.analysis_agent: Optional[SkillBasedAgent] = None
        self.remediation_agent: Optional[SkillBasedAgent] = None
        self.initialized = False
        self.violation_count = 0
        self.event_count = 0
        logger.info("Skill-based detection system created")
    
    async def initialize(self, controls: List[Dict[str, Any]], broadcast_new_skills: bool = False):
        """
        Initialize the detection system with compliance controls
        
        Args:
            controls: List of compliance controls to create detection skills from
            broadcast_new_skills: Whether to broadcast new skill acquisitions via WebSocket
        """
        try:
            logger.info(f"Initializing skill-based detection system with {len(controls)} controls")
            
            # Get or create skill registry
            self.skill_registry = get_skill_registry()
            
            # Get skill persistence
            skill_persistence = get_skill_persistence()
            
            # Track new skills for broadcasting
            new_skills = []
            
            # Create detection skills from controls
            detection_skills = create_detection_skills_from_controls(controls)
            
            # Register detection skills and persist metadata
            for skill in detection_skills:
                # Check if this is a new skill
                existing_skill = skill_persistence.get_skill(skill.skill_id)
                is_new = existing_skill is None
                
                # Create skill metadata
                control = next((c for c in controls if f"detect_{c.get('control_id', '').replace('.', '_').replace('-', '_').lower()}" == skill.skill_id), None)
                skill_metadata = SkillMetadata(
                    skill_id=skill.skill_id,
                    name=skill.name,
                    description=skill.description,
                    category=skill.category.value,
                    control_id=control.get('control_id') if control else None,
                    standard=control.get('standard') if control else None,
                    severity=control.get('severity') if control else None,
                    enabled=existing_skill.enabled if existing_skill else True
                )
                
                # Persist skill metadata
                skill_persistence.add_skill(skill_metadata)
                
                # Only register if enabled
                if skill_metadata.enabled:
                    self.skill_registry.register(skill)
                    
                    # Track new skills for broadcasting
                    if is_new and broadcast_new_skills:
                        new_skills.append(skill_metadata.to_dict())
                else:
                    logger.info(f"Skipping disabled skill: {skill.skill_id}")
            
            # Register COS policy drift detection skill
            self.skill_registry.register(COSPolicyDriftDetectionSkill())
            
            # Register analysis skills
            self.skill_registry.register(SecurityImpactAnalysisSkill())
            self.skill_registry.register(PolicyDriftImpactAnalysisSkill())
            
            # Register remediation skills
            self.skill_registry.register(RemediationGenerationSkill())
            self.skill_registry.register(ApprovalBasedRemediationSkill())
            
            # Create skill-based agents
            self.detection_agent = SkillBasedAgent(
                role="detection",
                skills=self.skill_registry.list_by_category(SkillCategory.DETECTION),
                skill_registry=self.skill_registry
            )
            
            self.analysis_agent = SkillBasedAgent(
                role="analysis",
                skills=self.skill_registry.list_by_category(SkillCategory.ANALYSIS),
                skill_registry=self.skill_registry
            )
            
            self.remediation_agent = SkillBasedAgent(
                role="remediation",
                skills=self.skill_registry.list_by_category(SkillCategory.REMEDIATION),
                skill_registry=self.skill_registry
            )
            
            self.initialized = True
            
            stats = self.skill_registry.get_stats()
            logger.info(f"Detection system initialized: {stats['total_skills']} skills registered")
            logger.info(f"Skills by category: {stats['by_category']}")
            
            # Broadcast new skills acquired
            if new_skills and broadcast_new_skills:
                await self._broadcast_skills_acquired(new_skills)
            
        except Exception as e:
            logger.error(f"Failed to initialize detection system: {e}", exc_info=True)
            raise
    
    async def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single event through the detection system
        
        Args:
            event: Event to process
            
        Returns:
            Processing results including violations detected
        """
        if not self.initialized:
            logger.warning("Detection system not initialized, skipping event")
            return {'error': 'System not initialized'}
        
        self.event_count += 1
        
        try:
            context = {'event': event}
            results = {
                'event': event,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'violations': [],
                'analysis': [],
                'remediation': []
            }
            
            # Detection phase
            detection_results = self.detection_agent.process(context)
            
            for detection in detection_results:
                if detection.violation_detected:
                    self.violation_count += 1
                    violation = detection.details
                    
                    logger.info(
                        f"Violation detected: {violation.get('control_id')} - "
                        f"{violation.get('control_description', '')[:50]}"
                    )
                    
                    results['violations'].append(violation)
                    
                    # Analysis phase
                    analysis_context = {
                        'event': event,
                        'previous_result': detection.to_dict()
                    }
                    analysis_results = self.analysis_agent.process(analysis_context)
                    
                    for analysis in analysis_results:
                        results['analysis'].append(analysis.details)
                    
                    # Remediation phase
                    remediation_context = {
                        'event': event,
                        'previous_result': detection.to_dict(),
                        'analysis': [a.details for a in analysis_results]
                    }
                    remediation_results = self.remediation_agent.process(remediation_context)
                    
                    for remediation in remediation_results:
                        results['remediation'].append(remediation.details)
                    
                    # Record violation in tracker
                    tracker = get_tracker()
                    tracker.record_violation(violation, event)
                    
                    # Broadcast to WebSocket
                    await self._broadcast_violation(event, violation, results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing event: {e}", exc_info=True)
            return {'error': str(e), 'event': event}
    
    async def _broadcast_violation(
        self,
        event: Dict[str, Any],
        violation: Dict[str, Any],
        results: Dict[str, Any]
    ):
        """Broadcast violation to WebSocket clients"""
        try:
            message = {
                'type': 'violation_detected',
                'data': {
                    'control_id': violation.get('control_id'),
                    'description': violation.get('control_description'),
                    'severity': violation.get('severity'),
                    'standard': violation.get('standard'),
                    'category': violation.get('category'),
                    'event': {
                        'source': event.get('source'),
                        'event_name': event.get('event_name'),
                        'resource_type': event.get('resource_type'),
                        'resource_name': event.get('resource_name'),
                        'timestamp': event.get('event_time')
                    },
                    'analysis': results.get('analysis', []),
                    'remediation': results.get('remediation', []),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            }
            
            await ws_manager.broadcast(message)
            
        except Exception as e:
            logger.error(f"Error broadcasting violation: {e}")
    
    async def _broadcast_skills_acquired(self, skills: List[Dict[str, Any]]):
        """Broadcast newly acquired skills to WebSocket clients"""
        try:
            message = {
                'type': 'skills_acquired',
                'data': {
                    'skills': skills,
                    'count': len(skills),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            }
            
            await ws_manager.broadcast(message)
            logger.info(f"Broadcasted {len(skills)} newly acquired skills")
            
        except Exception as e:
            logger.error(f"Error broadcasting skills acquired: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get detection system statistics"""
        stats = {
            'initialized': self.initialized,
            'events_processed': self.event_count,
            'violations_detected': self.violation_count,
            'violation_rate': (self.violation_count / self.event_count * 100) if self.event_count > 0 else 0
        }
        
        if self.initialized:
            stats['skill_registry'] = self.skill_registry.get_stats()
            stats['detection_agent'] = self.detection_agent.get_stats()
            stats['analysis_agent'] = self.analysis_agent.get_stats()
            stats['remediation_agent'] = self.remediation_agent.get_stats()
        
        return stats
    
    async def reload_controls(self, controls: List[Dict[str, Any]], broadcast_new_skills: bool = True):
        """
        Reload detection skills from updated controls
        
        Args:
            controls: Updated list of compliance controls
            broadcast_new_skills: Whether to broadcast new skill acquisitions
        """
        logger.info(f"Reloading detection system with {len(controls)} controls")
        await self.initialize(controls, broadcast_new_skills=broadcast_new_skills)


# Global detection system instance
_detection_system: Optional[SkillBasedDetectionSystem] = None


def get_detection_system() -> SkillBasedDetectionSystem:
    """Get or create global detection system instance"""
    global _detection_system
    if _detection_system is None:
        _detection_system = SkillBasedDetectionSystem()
    return _detection_system


async def initialize_detection_system_from_vector_store():
    """
    Initialize detection system from controls in vector store
    """
    try:
        vector_store = get_vector_store()
        
        # Get all controls from vector store
        controls = []
        if hasattr(vector_store, 'controls_map'):
            controls = list(vector_store.controls_map.values())
        
        if not controls:
            logger.warning("No controls found in vector store, detection system will have no skills")
            return
        
        # Initialize detection system
        detection_system = get_detection_system()
        await detection_system.initialize(controls)
        
        logger.info(f"Detection system initialized with {len(controls)} controls from vector store")
        
    except Exception as e:
        logger.error(f"Failed to initialize detection system from vector store: {e}", exc_info=True)
        raise