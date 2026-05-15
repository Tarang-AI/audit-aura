"""
Evidence Manager Service
Manages evidence files for compliance violations
"""
import json
import logging
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


class EvidenceManager:
    """Manages evidence files and metadata"""
    
    def __init__(self, data_dir: str = "./data/evidence"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.evidence_metadata: List[Dict[str, Any]] = []
        self._load_metadata()
    
    def _load_metadata(self):
        """Load evidence metadata from disk"""
        metadata_file = self.data_dir / "evidence_metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    self.evidence_metadata = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load evidence metadata: {e}")
                self.evidence_metadata = []
    
    def _save_metadata(self):
        """Save evidence metadata to disk"""
        metadata_file = self.data_dir / "evidence_metadata.json"
        try:
            with open(metadata_file, 'w') as f:
                json.dump(self.evidence_metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save evidence metadata: {e}")
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def store_evidence(
        self,
        violation_id: str,
        control_id: str,
        file_path: str,
        description: str,
        uploaded_by: str = "system"
    ) -> Dict[str, Any]:
        """
        Store evidence file for a violation
        
        Args:
            violation_id: ID of the violation
            control_id: Control ID
            file_path: Path to the evidence file
            description: Description of the evidence
            uploaded_by: User who uploaded the evidence
            
        Returns:
            Evidence metadata
        """
        source_path = Path(file_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Evidence file not found: {file_path}")
        
        timestamp = datetime.now(timezone.utc)
        evidence_id = f"evidence_{timestamp.strftime('%Y%m%d_%H%M%S')}_{violation_id}"
        
        # Create violation-specific directory
        violation_dir = self.data_dir / violation_id
        violation_dir.mkdir(exist_ok=True)
        
        # Copy file to evidence directory
        dest_path = violation_dir / source_path.name
        shutil.copy2(source_path, dest_path)
        
        # Calculate file hash for integrity
        file_hash = self._calculate_file_hash(dest_path)
        
        # Create metadata
        metadata = {
            'id': evidence_id,
            'violation_id': violation_id,
            'control_id': control_id,
            'file_name': source_path.name,
            'file_path': str(dest_path),
            'file_size': dest_path.stat().st_size,
            'file_hash': file_hash,
            'description': description,
            'uploaded_by': uploaded_by,
            'uploaded_at': timestamp.isoformat(),
            'verified': False
        }
        
        self.evidence_metadata.append(metadata)
        self._save_metadata()
        
        logger.info(f"Stored evidence: {evidence_id}")
        return metadata
    
    def get_evidence_by_violation(self, violation_id: str) -> List[Dict[str, Any]]:
        """Get all evidence for a specific violation"""
        return [e for e in self.evidence_metadata if e['violation_id'] == violation_id]
    
    def get_evidence(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        """Get evidence metadata by ID"""
        for evidence in self.evidence_metadata:
            if evidence['id'] == evidence_id:
                return evidence
        return None
    
    def verify_evidence(self, evidence_id: str, verified_by: str) -> bool:
        """Mark evidence as verified"""
        for evidence in self.evidence_metadata:
            if evidence['id'] == evidence_id:
                # Verify file integrity
                file_path = Path(evidence['file_path'])
                if not file_path.exists():
                    logger.error(f"Evidence file not found: {file_path}")
                    return False
                
                current_hash = self._calculate_file_hash(file_path)
                if current_hash != evidence['file_hash']:
                    logger.error(f"Evidence file integrity check failed: {evidence_id}")
                    return False
                
                evidence['verified'] = True
                evidence['verified_by'] = verified_by
                evidence['verified_at'] = datetime.now(timezone.utc).isoformat()
                self._save_metadata()
                logger.info(f"Verified evidence: {evidence_id}")
                return True
        
        return False
    
    def delete_evidence(self, evidence_id: str) -> bool:
        """Delete evidence file and metadata"""
        evidence = self.get_evidence(evidence_id)
        if not evidence:
            return False
        
        # Delete file
        try:
            file_path = Path(evidence['file_path'])
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.error(f"Failed to delete evidence file: {e}")
            return False
        
        # Remove from metadata
        self.evidence_metadata = [e for e in self.evidence_metadata if e['id'] != evidence_id]
        self._save_metadata()
        
        logger.info(f"Deleted evidence: {evidence_id}")
        return True
    
    def get_evidence_summary(self) -> Dict[str, Any]:
        """Get summary of evidence storage"""
        total_size = sum(e.get('file_size', 0) for e in self.evidence_metadata)
        verified_count = len([e for e in self.evidence_metadata if e.get('verified', False)])
        
        return {
            'total_evidence': len(self.evidence_metadata),
            'verified_evidence': verified_count,
            'total_size_bytes': total_size,
            'violations_with_evidence': len(set(e['violation_id'] for e in self.evidence_metadata))
        }


# Singleton instance
_evidence_manager: Optional[EvidenceManager] = None


def get_evidence_manager() -> EvidenceManager:
    """Get or create evidence manager singleton"""
    global _evidence_manager
    if _evidence_manager is None:
        _evidence_manager = EvidenceManager()
    return _evidence_manager