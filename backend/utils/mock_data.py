"""
Mock Data Service
Handles loading and managing mock data from JSON store with live score simulation
"""
import json
import os
import random
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timezone

class MockDataService:
    """Service for managing mock data with live compliance score simulation"""
    
    def __init__(self, data_path: str = "./data/mock_data.json"):
        self.data_path = data_path
        self._data = None
        self._current_score = None
        self._last_update = None
        self._load_data()
    
    def _load_data(self):
        """Load mock data from JSON file"""
        try:
            if os.path.exists(self.data_path):
                with open(self.data_path, 'r') as f:
                    self._data = json.load(f)
                    self._current_score = self._data.get("compliance_scores", {}).get("overall", 0.85)
            else:
                # Create default mock data if file doesn't exist
                self._data = self._get_default_data()
                self._current_score = 0.85
                self._save_data()
        except Exception as e:
            print(f"Error loading mock data: {e}")
            self._data = self._get_default_data()
            self._current_score = 0.85
    
    def _save_data(self):
        """Save mock data to JSON file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            with open(self.data_path, 'w') as f:
                json.dump(self._data, f, indent=2)
        except Exception as e:
            print(f"Error saving mock data: {e}")
    
    def _get_default_data(self) -> Dict[str, Any]:
        """Get default mock data structure"""
        return {
            "violations": [],
            "compliance_scores": {
                "overall": 0.85,
                "by_standard": {}
            },
            "standards": [],
            "recent_events": [],
            "security_metrics": {},
            "live_score_simulation": {
                "enabled": True,
                "update_interval_seconds": 30,
                "score_variations": [-0.02, -0.01, 0, 0, 0, 0.01, 0.02],
                "min_score": 0.70,
                "max_score": 0.95
            }
        }
    
    def get_violations(self, status: Optional[str] = None, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get violations with optional filtering"""
        violations = self._data.get("violations", [])
        
        if status:
            violations = [v for v in violations if v.get("status") == status]
        
        if severity:
            violations = [v for v in violations if v.get("severity") == severity]
        
        return violations
    
    def get_violation_by_id(self, violation_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific violation by ID"""
        violations = self._data.get("violations", [])
        for v in violations:
            if v.get("id") == violation_id:
                return v
        return None
    
    def get_compliance_scores(self, live: bool = False) -> Dict[str, Any]:
        """Get compliance scores with optional live simulation"""
        scores = self._data.get("compliance_scores", {"overall": 0.85, "by_standard": {}})
        
        if live and self._should_update_score():
            self._update_live_score()
            scores = scores.copy()
            scores["overall_score"] = self._current_score
        else:
            scores["overall_score"] = scores.get("overall", 0.85)
        
        # Transform by_standard into standards format expected by frontend
        standards_dict = {}
        by_standard = scores.get("by_standard", {})
        standards_list = self._data.get("standards", [])
        
        for standard in standards_list:
            std_name = standard.get("name", "")
            # Use the score from by_standard if available, otherwise from the standard itself
            std_score = by_standard.get(std_name, standard.get("score", 0))
            
            # Count violations for this standard
            violations = self.get_violations()
            std_violations = len([v for v in violations if v.get("standard") == std_name])
            
            standards_dict[std_name] = {
                "score": std_score,
                "violations": std_violations,
                "controls": standard.get("total_controls", 0)
            }
        
        scores["standards"] = standards_dict
        scores["total_controls"] = sum(s.get("total_controls", 0) for s in standards_list)
        scores["total_violations"] = len(self.get_violations())
        
        return scores
    
    def _should_update_score(self) -> bool:
        """Check if score should be updated based on interval"""
        config = self._data.get("live_score_simulation", {})
        if not config.get("enabled", False):
            return False
        
        if self._last_update is None:
            self._last_update = datetime.now(timezone.utc)
            return True
        
        interval = config.get("update_interval_seconds", 30)
        elapsed = (datetime.now(timezone.utc) - self._last_update).total_seconds()
        
        if elapsed >= interval:
            self._last_update = datetime.now(timezone.utc)
            return True
        
        return False
    
    def _update_live_score(self):
        """Update the live compliance score with random variation"""
        config = self._data.get("live_score_simulation", {})
        variations = config.get("score_variations", [-2, -1, 0, 0, 0, 1, 2])
        min_score = config.get("min_score", 70)
        max_score = config.get("max_score", 95)
        
        # Apply random variation
        variation = random.choice(variations)
        new_score = self._current_score + variation
        
        # Clamp to min/max
        self._current_score = max(min_score, min(max_score, new_score))
    
    def get_standards(self) -> List[Dict[str, Any]]:
        """Get all standards"""
        return self._data.get("standards", [])
    
    def get_recent_events(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get recent events with optional limit"""
        events = self._data.get("recent_events", [])
        if limit:
            return events[:limit]
        return events
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics"""
        return self._data.get("security_metrics", {})
    
    def get_cloud_event_trackers(self) -> List[Dict[str, Any]]:
        """Get configured cloud connections (event trackers)"""
        return self._data.get("cloud_connections", [])
    
    def get_dashboard_data(self, role: str = "admin") -> Dict[str, Any]:
        """Get all data for dashboard based on role"""
        base_data = {
            "compliance_score": self.get_compliance_scores(live=True),
            "violations": self.get_violations(),
            "standards": self.get_standards(),
            "recent_events": self.get_recent_events(limit=10),
            "cloud_connections": self.get_cloud_event_trackers()
        }
        
        # Add role-specific data
        if role in ["admin", "security"]:
            base_data["security_metrics"] = self.get_security_metrics()
        
        return base_data
    
    def get_violation_stats(self) -> Dict[str, Any]:
        """Get violation statistics"""
        violations = self.get_violations()
        
        stats = {
            "total": len(violations),
            "by_severity": {
                "critical": len([v for v in violations if v.get("severity") == "critical"]),
                "high": len([v for v in violations if v.get("severity") == "high"]),
                "medium": len([v for v in violations if v.get("severity") == "medium"]),
                "low": len([v for v in violations if v.get("severity") == "low"])
            },
            "by_status": {
                "open": len([v for v in violations if v.get("status") == "open"]),
                "in_progress": len([v for v in violations if v.get("status") == "in_progress"]),
                "resolved": len([v for v in violations if v.get("status") == "resolved"])
            },
            "by_standard": {}
        }
        
        # Count by standard
        for v in violations:
            standard = v.get("standard", "Unknown")
            stats["by_standard"][standard] = stats["by_standard"].get(standard, 0) + 1
        
        return stats
    
    def add_violation(self, violation: Dict[str, Any]):
        """Add a new violation"""
        if "violations" not in self._data:
            self._data["violations"] = []
        self._data["violations"].insert(0, violation)
        self._save_data()
    
    def update_compliance_score(self, standard: str, score: float):
        """Update compliance score for a standard"""
        if "compliance_scores" not in self._data:
            self._data["compliance_scores"] = {"overall": 85, "by_standard": {}}
        
        self._data["compliance_scores"]["by_standard"][standard] = score
        
        # Recalculate overall score
        scores = list(self._data["compliance_scores"]["by_standard"].values())
        if scores:
            self._data["compliance_scores"]["overall"] = sum(scores) / len(scores)
            self._current_score = self._data["compliance_scores"]["overall"]
        
        self._save_data()
    
    def reload(self):
        """Reload data from file"""
        self._load_data()


# Global instance
_mock_data_service = None

def get_mock_data_service(data_path: str = "./data/mock_data.json") -> MockDataService:
    """Get or create mock data service instance"""
    global _mock_data_service
    if _mock_data_service is None:
        _mock_data_service = MockDataService(data_path)
    return _mock_data_service