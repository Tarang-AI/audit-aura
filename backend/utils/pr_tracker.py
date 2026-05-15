"""
GitHub PR Tracker Service
Tracks pull requests related to compliance violations and monitors their status
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class PRTracker:
    """Tracks GitHub PRs related to compliance violations"""
    
    def __init__(self, data_path: str = "./data/pr_tracking.json"):
        self.data_path = data_path
        self._data = {
            "prs": [],
            "violation_pr_links": {}
        }
        self._load_data()
    
    def _load_data(self):
        """Load PR tracking data from JSON file"""
        try:
            if Path(self.data_path).exists():
                with open(self.data_path, 'r') as f:
                    self._data = json.load(f)
                logger.info(f"Loaded {len(self._data.get('prs', []))} PRs from storage")
            else:
                self._save_data()
        except Exception as e:
            logger.error(f"Error loading PR tracking data: {e}")
    
    def _save_data(self):
        """Save PR tracking data to JSON file"""
        try:
            Path(self.data_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.data_path, 'w') as f:
                json.dump(self._data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving PR tracking data: {e}")
    
    def link_pr_to_violation(
        self,
        pr_url: str,
        pr_number: int,
        violation_id: str,
        title: str,
        description: str = "",
        author: str = "",
        repository: str = ""
    ) -> Dict[str, Any]:
        """
        Link a PR to a compliance violation
        
        Args:
            pr_url: Full URL to the PR
            pr_number: PR number
            violation_id: ID of the violation this PR addresses
            title: PR title
            description: PR description
            author: PR author
            repository: Repository name
            
        Returns:
            Created PR record
        """
        pr_record = {
            "id": f"pr-{pr_number}-{violation_id}",
            "pr_url": pr_url,
            "pr_number": pr_number,
            "violation_id": violation_id,
            "title": title,
            "description": description,
            "author": author,
            "repository": repository,
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "merged_at": None,
            "closed_at": None,
            "files_changed": [],
            "commits": 0,
            "additions": 0,
            "deletions": 0,
            "reviewers": [],
            "labels": ["compliance", "security"]
        }
        
        # Add PR to list
        self._data["prs"].append(pr_record)
        
        # Link violation to PR
        if violation_id not in self._data["violation_pr_links"]:
            self._data["violation_pr_links"][violation_id] = []
        self._data["violation_pr_links"][violation_id].append(pr_record["id"])
        
        self._save_data()
        logger.info(f"Linked PR #{pr_number} to violation {violation_id}")
        
        return pr_record
    
    def update_pr_status(
        self,
        pr_id: str,
        status: str,
        merged_at: Optional[str] = None,
        closed_at: Optional[str] = None
    ):
        """
        Update PR status
        
        Args:
            pr_id: PR ID
            status: New status (open, merged, closed)
            merged_at: Merge timestamp
            closed_at: Close timestamp
        """
        for pr in self._data["prs"]:
            if pr["id"] == pr_id:
                pr["status"] = status
                pr["updated_at"] = datetime.now(timezone.utc).isoformat()
                
                if merged_at:
                    pr["merged_at"] = merged_at
                if closed_at:
                    pr["closed_at"] = closed_at
                
                self._save_data()
                logger.info(f"Updated PR {pr_id} status to {status}")
                return pr
        
        logger.warning(f"PR {pr_id} not found")
        return None
    
    def get_prs_for_violation(self, violation_id: str) -> List[Dict[str, Any]]:
        """
        Get all PRs linked to a violation
        
        Args:
            violation_id: Violation ID
            
        Returns:
            List of PR records
        """
        pr_ids = self._data["violation_pr_links"].get(violation_id, [])
        return [pr for pr in self._data["prs"] if pr["id"] in pr_ids]
    
    def get_all_prs(
        self,
        status: Optional[str] = None,
        violation_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all PRs with optional filtering
        
        Args:
            status: Filter by status (open, merged, closed)
            violation_id: Filter by violation ID
            
        Returns:
            List of PR records
        """
        prs = self._data["prs"]
        
        if status:
            prs = [pr for pr in prs if pr["status"] == status]
        
        if violation_id:
            pr_ids = self._data["violation_pr_links"].get(violation_id, [])
            prs = [pr for pr in prs if pr["id"] in pr_ids]
        
        # Sort by created_at descending
        prs.sort(key=lambda x: x["created_at"], reverse=True)
        
        return prs
    
    def get_pr_by_id(self, pr_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific PR by ID
        
        Args:
            pr_id: PR ID
            
        Returns:
            PR record or None
        """
        for pr in self._data["prs"]:
            if pr["id"] == pr_id:
                return pr
        return None
    
    def get_pr_stats(self) -> Dict[str, Any]:
        """
        Get PR statistics
        
        Returns:
            Statistics about PRs
        """
        prs = self._data["prs"]
        
        return {
            "total": len(prs),
            "open": len([pr for pr in prs if pr["status"] == "open"]),
            "merged": len([pr for pr in prs if pr["status"] == "merged"]),
            "closed": len([pr for pr in prs if pr["status"] == "closed"]),
            "violations_with_prs": len(self._data["violation_pr_links"]),
            "average_prs_per_violation": (
                len(prs) / len(self._data["violation_pr_links"])
                if self._data["violation_pr_links"] else 0
            )
        }
    
    def verify_fix_on_merge(self, pr_id: str) -> Dict[str, Any]:
        """
        Verify if a merged PR fixes the related violation
        
        Args:
            pr_id: PR ID
            
        Returns:
            Verification result
        """
        pr = self.get_pr_by_id(pr_id)
        
        if not pr:
            return {
                "success": False,
                "message": "PR not found"
            }
        
        if pr["status"] != "merged":
            return {
                "success": False,
                "message": "PR not merged yet"
            }
        
        # In a real implementation, this would:
        # 1. Re-run compliance checks
        # 2. Verify the violation is resolved
        # 3. Update violation status
        # 4. Generate audit evidence
        
        return {
            "success": True,
            "message": f"PR #{pr['pr_number']} merged successfully",
            "violation_id": pr["violation_id"],
            "pr_url": pr["pr_url"],
            "merged_at": pr["merged_at"],
            "recommendation": "Re-run compliance scan to verify fix"
        }


# Singleton instance
_pr_tracker = None


def get_pr_tracker() -> PRTracker:
    """Get or create PR tracker instance"""
    global _pr_tracker
    if _pr_tracker is None:
        _pr_tracker = PRTracker()
    return _pr_tracker