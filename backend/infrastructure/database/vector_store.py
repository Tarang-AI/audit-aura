"""
Vector Store Service
Manages compliance control embeddings and similarity search
"""
import logging
import os
import pickle
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class VectorStore:
    """Vector store for compliance controls"""
    
    def __init__(self, store_path: str = "./data/vector_store"):
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
        self.store = None
        self.embeddings = None
        self.controls_map = {}  # Map index to control
        
    def initialize(self, openai_api_key: str | None = None):
        """Initialize embeddings and load existing store if available"""
        try:
            # Use HuggingFace embeddings (free, local, no API key needed)
            from langchain_huggingface import HuggingFaceEmbeddings
            
            logger.info("Initializing vector store with HuggingFace embeddings")
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            
            # Try to load existing store
            self._load_store()
            
            logger.info("Vector store initialized with HuggingFace embeddings")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    def build_from_controls(self, controls: List[Dict[str, Any]]) -> bool:
        """
        Build vector store from compliance controls
        
        Args:
            controls: List of compliance controls
            
        Returns:
            True if successful
        """
        try:
            from langchain_community.vectorstores import FAISS
            from langchain_core.documents import Document
            
            if not controls:
                logger.warning("No controls provided to build vector store")
                return False
            
            # Create documents from controls
            documents = []
            self.controls_map = {}
            
            for idx, control in enumerate(controls):
                # Create searchable text from control
                text = self._create_searchable_text(control)
                
                # Create document with metadata
                doc = Document(
                    page_content=text,
                    metadata={
                        'control_id': control.get('control_id', ''),
                        'title': control.get('title', ''),
                        'standard': control.get('standard', ''),
                        'category': control.get('category', ''),
                        'severity': control.get('severity', ''),
                        'index': idx
                    }
                )
                documents.append(doc)
                self.controls_map[idx] = control
            
            # Build FAISS index
            self.store = FAISS.from_documents(documents, self.embeddings)
            
            # Save store
            self._save_store()
            
            logger.info(f"Vector store built with {len(controls)} controls")
            return True
            
        except Exception as e:
            logger.error(f"Error building vector store: {e}")
            return False
            
    def add_controls(self, controls: List[Dict[str, Any]]) -> bool:
        """
        Add new controls to existing vector store
        
        Args:
            controls: List of new compliance controls
            
        Returns:
            True if successful
        """
        try:
            from langchain_core.documents import Document
            
            if not controls:
                return True
                
            # If store is empty, just build it
            if not self.store:
                return self.build_from_controls(controls)
                
            # Create documents from new controls
            documents = []
            start_idx = max(self.controls_map.keys()) + 1 if self.controls_map else 0
            
            for i, control in enumerate(controls):
                idx = start_idx + i
                text = self._create_searchable_text(control)
                
                doc = Document(
                    page_content=text,
                    metadata={
                        'control_id': control.get('control_id', ''),
                        'title': control.get('title', ''),
                        'standard': control.get('standard', ''),
                        'category': control.get('category', ''),
                        'severity': control.get('severity', ''),
                        'index': idx
                    }
                )
                documents.append(doc)
                self.controls_map[idx] = control
                
            # Add to FAISS index
            self.store.add_documents(documents)
            
            # Save updated store
            self._save_store()
            
            logger.info(f"Added {len(controls)} new controls to vector store (Total: {len(self.controls_map)})")
            return True
            
        except Exception as e:
            logger.error(f"Error adding to vector store: {e}")
            return False
    
    def search_similar_controls(
        self,
        query: str,
        k: int = 5,
        filter_standard: Optional[str] = None,
        filter_category: Optional[str] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search for similar controls
        
        Args:
            query: Search query
            k: Number of results to return
            filter_standard: Filter by audit standard
            filter_category: Filter by category
            
        Returns:
            List of (control, similarity_score) tuples
        """
        try:
            if not self.store:
                logger.warning("Vector store not initialized")
                return []
            
            # Perform similarity search
            results = self.store.similarity_search_with_score(query, k=k*2)
            
            # Filter and format results
            filtered_results = []
            for doc, score in results:
                idx = doc.metadata.get('index')
                if idx is None or idx not in self.controls_map:
                    continue
                
                control = self.controls_map[idx]
                
                # Apply filters
                if filter_standard and control.get('standard') != filter_standard:
                    continue
                if filter_category and control.get('category') != filter_category:
                    continue
                
                filtered_results.append((control, float(score)))
                
                if len(filtered_results) >= k:
                    break
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []
    
    def find_relevant_controls(
        self,
        event: Dict[str, Any],
        k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find controls relevant to an event
        
        Args:
            event: Event data
            k: Number of controls to return
            
        Returns:
            List of relevant controls
        """
        try:
            # Create query from event
            query = self._create_event_query(event)
            
            # Search for similar controls
            results = self.search_similar_controls(query, k=k)
            
            # Return just the controls (without scores)
            return [control for control, _ in results]
            
        except Exception as e:
            logger.error(f"Error finding relevant controls: {e}")
            return []
    
    def get_all_controls(self) -> List[Dict[str, Any]]:
        """Get all controls in the store"""
        return list(self.controls_map.values())
    
    def get_controls_by_standard(self, standard: str) -> List[Dict[str, Any]]:
        """Get all controls for a specific standard"""
        return [
            control for control in self.controls_map.values()
            if control.get('standard') == standard
        ]
    
    def get_controls_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all controls for a specific category"""
        return [
            control for control in self.controls_map.values()
            if control.get('category') == category
        ]
    
    def _create_searchable_text(self, control: Dict[str, Any]) -> str:
        """Create searchable text from control"""
        parts = [
            f"Control ID: {control.get('control_id', '')}",
            f"Title: {control.get('title', '')}",
            f"Standard: {control.get('standard', '')}",
            f"Category: {control.get('category', '')}",
            f"Description: {control.get('description', '')}",
            f"Severity: {control.get('severity', '')}",
            f"Remediation: {control.get('remediation', '')}"
        ]
        return "\n".join(parts)
    
    def _create_event_query(self, event: Dict[str, Any]) -> str:
        """Create search query from event"""
        parts = []
        
        # Add event type/name
        if 'event_name' in event:
            parts.append(f"Event: {event['event_name']}")
        
        # Add resource type
        if 'resource_type' in event:
            parts.append(f"Resource: {event['resource_type']}")
        
        # Add source
        if 'source' in event:
            parts.append(f"Source: {event['source']}")
        
        # Add key attributes
        for key in ['public', 'encryption_enabled', 'backup_enabled', 'allows_all_traffic']:
            if key in event:
                parts.append(f"{key}: {event[key]}")
        
        return " ".join(parts)
    
    def _save_store(self):
        """Save vector store to disk"""
        try:
            if not self.store:
                return
            
            # Save FAISS index
            faiss_path = self.store_path / "faiss_index"
            self.store.save_local(str(faiss_path))
            
            # Save controls map
            controls_path = self.store_path / "controls_map.pkl"
            with open(controls_path, 'wb') as f:
                pickle.dump(self.controls_map, f)
            
            logger.info(f"Vector store saved to {self.store_path}")
            
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")
    
    def _load_store(self):
        """Load vector store from disk"""
        try:
            from langchain_community.vectorstores import FAISS
            
            faiss_path = self.store_path / "faiss_index"
            controls_path = self.store_path / "controls_map.pkl"
            
            if not faiss_path.exists() or not controls_path.exists():
                logger.info("No existing vector store found")
                return
            
            # Load FAISS index
            self.store = FAISS.load_local(
                str(faiss_path),
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            
            # Load controls map
            with open(controls_path, 'rb') as f:
                self.controls_map = pickle.load(f)
            
            logger.info(f"Vector store loaded from {self.store_path}")
            
        except Exception as e:
            logger.warning(f"Could not load existing vector store: {e}")


# Global vector store instance
_vector_store: Optional[VectorStore] = None


def get_vector_store(store_path: str = "./data/vector_store") -> VectorStore:
    """Get or create global vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore(store_path)
    return _vector_store


def build_store(texts: List[str], openai_api_key: Optional[str] = None) -> Optional[VectorStore]:
    """
    Legacy function for backward compatibility
    
    Args:
        texts: List of text descriptions
        openai_api_key: OpenAI API key
        
    Returns:
        Vector store instance
    """
    try:
        api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OpenAI API key not provided")
            return None
        
        store = get_vector_store()
        store.initialize(api_key)
        
        # Convert texts to simple controls
        controls = [
            {
                'control_id': f'CTRL-{i}',
                'description': text,
                'standard': 'Unknown',
                'category': 'General',
                'severity': 'medium'
            }
            for i, text in enumerate(texts)
        ]
        
        store.build_from_controls(controls)
        return store
        
    except Exception as e:
        logger.error(f"Error building store: {e}")
        return None

# Made with Bob
