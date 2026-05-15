"""
Skill persistence model
Stores skill metadata and enable/disable state
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class SkillMetadata:
    """Metadata for a skill including enable/disable state"""
    
    def __init__(
        self,
        skill_id: str,
        name: str,
        description: str,
        category: str,
        control_id: Optional[str] = None,
        standard: Optional[str] = None,
        severity: Optional[str] = None,
        enabled: bool = True,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None
    ):
        self.skill_id = skill_id
        self.name = name
        self.description = description
        self.category = category
        self.control_id = control_id
        self.standard = standard
        self.severity = severity
        self.enabled = enabled
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.updated_at = updated_at or datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'skill_id': self.skill_id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'control_id': self.control_id,
            'standard': self.standard,
            'severity': self.severity,
            'enabled': self.enabled,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SkillMetadata':
        """Create from dictionary"""
        return cls(**data)


class SkillPersistence:
    """Manages skill persistence to disk"""
    
    def __init__(self, storage_path: str = "./data/skills.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.skills: Dict[str, SkillMetadata] = {}
        self._load()
    
    def _load(self):
        """Load skills from disk"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.skills = {
                        skill_id: SkillMetadata.from_dict(skill_data)
                        for skill_id, skill_data in data.items()
                    }
                logger.info(f"Loaded {len(self.skills)} skills from {self.storage_path}")
            except Exception as e:
                logger.error(f"Failed to load skills: {e}")
                self.skills = {}
        else:
            logger.info("No existing skills file found, starting fresh")
    
    def _save(self):
        """Save skills to disk"""
        try:
            data = {
                skill_id: skill.to_dict()
                for skill_id, skill in self.skills.items()
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(self.skills)} skills to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save skills: {e}")
    
    def add_skill(self, skill_metadata: SkillMetadata) -> bool:
        """Add or update a skill"""
        try:
            self.skills[skill_metadata.skill_id] = skill_metadata
            self._save()
            return True
        except Exception as e:
            logger.error(f"Failed to add skill {skill_metadata.skill_id}: {e}")
            return False
    
    def get_skill(self, skill_id: str) -> Optional[SkillMetadata]:
        """Get skill by ID"""
        return self.skills.get(skill_id)
    
    def list_all(self) -> List[SkillMetadata]:
        """List all skills"""
        return list(self.skills.values())
    
    def list_enabled(self) -> List[SkillMetadata]:
        """List only enabled skills"""
        return [skill for skill in self.skills.values() if skill.enabled]
    
    def enable_skill(self, skill_id: str) -> bool:
        """Enable a skill"""
        skill = self.skills.get(skill_id)
        if skill:
            skill.enabled = True
            skill.updated_at = datetime.now(timezone.utc).isoformat()
            self._save()
            logger.info(f"Enabled skill: {skill_id}")
            return True
        return False
    
    def disable_skill(self, skill_id: str) -> bool:
        """Disable a skill"""
        skill = self.skills.get(skill_id)
        if skill:
            skill.enabled = False
            skill.updated_at = datetime.now(timezone.utc).isoformat()
            self._save()
            logger.info(f"Disabled skill: {skill_id}")
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get skill statistics"""
        total = len(self.skills)
        enabled = sum(1 for s in self.skills.values() if s.enabled)
        disabled = total - enabled
        
        by_category = {}
        by_standard = {}
        
        for skill in self.skills.values():
            # Count by category
            by_category[skill.category] = by_category.get(skill.category, 0) + 1
            
            # Count by standard
            if skill.standard:
                by_standard[skill.standard] = by_standard.get(skill.standard, 0) + 1
        
        return {
            'total_skills': total,
            'enabled_skills': enabled,
            'disabled_skills': disabled,
            'by_category': by_category,
            'by_standard': by_standard
        }


# Global instance
_skill_persistence: Optional[SkillPersistence] = None


def get_skill_persistence() -> SkillPersistence:
    """Get or create global skill persistence instance"""
    global _skill_persistence
    if _skill_persistence is None:
        _skill_persistence = SkillPersistence()
    return _skill_persistence