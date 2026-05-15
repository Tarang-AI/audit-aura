"""
Agent Skills System
Implements skill-based architecture for detection, analysis, and remediation
"""
import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime, timezone
from abc import ABC, abstractmethod
import json

logger = logging.getLogger(__name__)


class SkillCategory(Enum):
    """Skill categories"""
    DETECTION = "detection"
    ANALYSIS = "analysis"
    REMEDIATION = "remediation"
    COMMUNICATION = "communication"
    VALIDATION = "validation"


class SkillResult:
    """Result of skill execution"""
    
    def __init__(
        self,
        success: bool,
        applicable: bool,
        violation_detected: Optional[bool] = None,
        severity: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        requires_followup: bool = False,
        followup_skills: Optional[List[str]] = None
    ):
        self.success = success
        self.applicable = applicable
        self.violation_detected = violation_detected
        self.severity = severity
        self.details = details or {}
        self.requires_followup = requires_followup
        self.followup_skills = followup_skills or []
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'success': self.success,
            'applicable': self.applicable,
            'violation_detected': self.violation_detected,
            'severity': self.severity,
            'details': self.details,
            'requires_followup': self.requires_followup,
            'followup_skills': self.followup_skills,
            'timestamp': self.timestamp
        }


class Skill(ABC):
    """Base class for agent skills"""
    
    skill_id: str = ""
    name: str = ""
    description: str = ""
    category: SkillCategory = SkillCategory.DETECTION
    required_capabilities: List[str] = []
    provider: Optional[str] = None  # 'ibm_cloud', 'aws', 'azure', 'all'
    
    @abstractmethod
    def is_applicable(self, context: Dict[str, Any]) -> bool:
        """Check if skill applies to this context"""
        pass
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> SkillResult:
        """Execute the skill"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert skill to dictionary"""
        return {
            'skill_id': self.skill_id,
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'required_capabilities': self.required_capabilities,
            'provider': self.provider
        }


class SkillRegistry:
    """Central registry for all skills"""
    
    def __init__(self):
        self._skills: Dict[str, Skill] = {}
        logger.info("Skill registry initialized")
    
    def register(self, skill: Skill):
        """Register a new skill"""
        if not skill.skill_id:
            raise ValueError(f"Skill must have a skill_id: {skill.__class__.__name__}")
        
        self._skills[skill.skill_id] = skill
        logger.info(f"Registered skill: {skill.skill_id} ({skill.name})")
    
    def get(self, skill_id: str) -> Optional[Skill]:
        """Get skill by ID"""
        return self._skills.get(skill_id)
    
    def list_all(self) -> List[Skill]:
        """List all skills"""
        return list(self._skills.values())
    
    def list_by_category(self, category: SkillCategory) -> List[Skill]:
        """List skills by category"""
        return [skill for skill in self._skills.values() if skill.category == category]
    
    def list_by_provider(self, provider: str) -> List[Skill]:
        """List skills for specific cloud provider"""
        return [
            skill for skill in self._skills.values()
            if skill.provider == provider or skill.provider == 'all'
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        stats = {
            'total_skills': len(self._skills),
            'by_category': {},
            'by_provider': {}
        }
        
        for skill in self._skills.values():
            # Count by category
            category = skill.category.value
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
            
            # Count by provider
            provider = skill.provider or 'all'
            stats['by_provider'][provider] = stats['by_provider'].get(provider, 0) + 1
        
        return stats


class SkillBasedAgent:
    """Agent that executes skills based on context"""
    
    def __init__(
        self,
        role: str,
        skills: List[Skill],
        skill_registry: SkillRegistry
    ):
        self.role = role
        self.skills = skills
        self.skill_registry = skill_registry
        self.execution_history: List[Dict[str, Any]] = []
        logger.info(f"Skill-based agent initialized: {role} with {len(skills)} skills")
    
    def process(self, context: Dict[str, Any]) -> List[SkillResult]:
        """Process context through applicable skills"""
        results = []
        
        # Execute applicable skills
        for skill in self.skills:
            try:
                if skill.is_applicable(context):
                    logger.info(f"Executing skill: {skill.name}")
                    result = skill.execute(context)
                    results.append(result)
                    
                    # Record execution
                    self._record_execution(skill, context, result)
                    
                    # Handle followup skills
                    if result.requires_followup and result.followup_skills:
                        followup_results = self._execute_followup_skills(
                            result.followup_skills,
                            context,
                            result
                        )
                        results.extend(followup_results)
            
            except Exception as e:
                logger.error(f"Error executing skill {skill.skill_id}: {e}", exc_info=True)
                results.append(SkillResult(
                    success=False,
                    applicable=True,
                    details={'error': str(e), 'skill_id': skill.skill_id}
                ))
        
        return results
    
    def _execute_followup_skills(
        self,
        skill_ids: List[str],
        context: Dict[str, Any],
        previous_result: SkillResult
    ) -> List[SkillResult]:
        """Execute followup skills"""
        results = []
        
        # Update context with previous result
        enhanced_context = {
            **context,
            'previous_result': previous_result.to_dict()
        }
        
        for skill_id in skill_ids:
            skill = self.skill_registry.get(skill_id)
            if skill and skill.is_applicable(enhanced_context):
                try:
                    logger.info(f"Executing followup skill: {skill.name}")
                    result = skill.execute(enhanced_context)
                    results.append(result)
                    self._record_execution(skill, enhanced_context, result)
                except Exception as e:
                    logger.error(f"Error executing followup skill {skill_id}: {e}")
        
        return results
    
    def _record_execution(
        self,
        skill: Skill,
        context: Dict[str, Any],
        result: SkillResult
    ):
        """Record skill execution for analytics"""
        execution_record = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'skill_id': skill.skill_id,
            'skill_name': skill.name,
            'category': skill.category.value,
            'success': result.success,
            'violation_detected': result.violation_detected,
            'severity': result.severity
        }
        
        self.execution_history.append(execution_record)
        
        # Keep only last 1000 executions
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        total_executions = len(self.execution_history)
        successful = sum(1 for e in self.execution_history if e['success'])
        violations = sum(1 for e in self.execution_history if e.get('violation_detected'))
        
        return {
            'role': self.role,
            'total_skills': len(self.skills),
            'total_executions': total_executions,
            'successful_executions': successful,
            'violations_detected': violations,
            'success_rate': (successful / total_executions * 100) if total_executions > 0 else 0
        }


class SkillChain:
    """Orchestrates execution of skill chains"""
    
    def __init__(self, skills: List[Skill]):
        self.skills = skills
    
    def execute(self, context: Dict[str, Any]) -> List[SkillResult]:
        """Execute skills in sequence"""
        results = []
        current_context = context.copy()
        
        for skill in self.skills:
            if skill.is_applicable(current_context):
                try:
                    result = skill.execute(current_context)
                    results.append(result)
                    
                    # Update context for next skill
                    current_context['previous_results'] = [r.to_dict() for r in results]
                    
                    # Stop chain if critical failure
                    if not result.success and skill.category == SkillCategory.DETECTION:
                        logger.warning(f"Stopping skill chain due to detection failure: {skill.skill_id}")
                        break
                
                except Exception as e:
                    logger.error(f"Error in skill chain at {skill.skill_id}: {e}")
                    break
        
        return results


# Registry moved to registry.py for better organization