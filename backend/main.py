"""
AuditAura - Continuous Compliance Guardian
Main FastAPI application
"""
import asyncio
import json
import logging
from typing import List, Optional
from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from pathlib import Path
from datetime import datetime, timezone

# Import configuration
from config import get_config

# Import infrastructure
from infrastructure.security.encryption import get_encryption_service

# Import services
from services.extractor import ComplianceExtractor
from services.vector_store import VectorStore, get_vector_store
from services.evaluator import evaluate_controls
from services.evidence import generate_evidence
from services.notifications import NotificationService
from services.event_sources import create_event_aggregator
from services.dynamic_event_sources import get_dynamic_source_manager
from services.compliance_tracker import get_tracker
from services.mock_data_service import get_mock_data_service
from services.pr_tracker import get_pr_tracker
from services.websocket_manager import ws_manager, start_heartbeat_task
from services.skill_based_detection_agent import (
    get_detection_system,
    initialize_detection_system_from_vector_store
)
from services.skills import get_skill_registry, SkillCategory

# Import routers
from routers.connections import router as connections_router
from routers.remediations import router as remediations_router
from routers.agents import router as agents_router

# Setup logging
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AuditAura",
    description="Continuous Compliance Guardian - Real-time AI-powered audit readiness",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(connections_router)
app.include_router(remediations_router)
app.include_router(agents_router)

# Setup PDF storage directory
PDF_STORAGE_DIR = Path("./data/pdfs")
PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Global state
config = None
extractor = None
vector_store = None
notification_service = None
event_aggregator = None
tracker = None
monitoring_task = None
detection_system = None


# Request/Response Models
class UploadResponse(BaseModel):
    success: bool
    message: str
    controls_count: int
    standards: List[str]


class ComplianceScoreResponse(BaseModel):
    overall_score: float
    standards: dict
    total_controls: int
    total_violations: int
    last_update: str


class HealthResponse(BaseModel):
    status: str
    version: str
    mock_mode: bool
    services: dict


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global config, extractor, vector_store, notification_service
    global event_aggregator, orchestrator, tracker, monitoring_task, detection_system
    
    try:
        # Load configuration
        config = get_config()
        logger.info("Configuration loaded successfully")
        
        # Initialize encryption service with config's encryption key
        encryption_service = get_encryption_service(encryption_key=config.encryption_key)
        logger.info("Encryption service initialized")
        
        # Initialize extractor with configurable extraction methods
        extractor = ComplianceExtractor(
            openai_api_key=config.openai_api_key,
            openai_enabled=config.openai_enabled,
            lm_studio_host=config.lm_studio_host,
            lm_studio_model=config.lm_studio_model,
            lm_studio_enabled=config.lm_studio_enabled,
            ollama_host=config.ollama_host,
            ollama_model=config.ollama_model,
            ollama_enabled=config.ollama_enabled
        )
        logger.info(f"Compliance extractor initialized (LM Studio: {config.lm_studio_enabled}, Ollama: {config.ollama_enabled}, OpenAI: {config.openai_enabled})")
        
        # Start WebSocket heartbeat task
        asyncio.create_task(start_heartbeat_task())
        logger.info("WebSocket heartbeat task started")
        
        # Initialize vector store
        vector_store = get_vector_store(config.vector_store_path)
        vector_store.initialize(config.openai_api_key)
        logger.info("Vector store initialized")
        
        # Initialize notification service
        notification_service = NotificationService(
            smtp_host=config.smtp_host,
            smtp_port=config.smtp_port,
            smtp_user=config.smtp_user,
            smtp_password=config.smtp_password,
            smtp_from=config.smtp_from,
            slack_webhook_url=config.slack_webhook_url
        )
        logger.info("Notification service initialized")
        
        # Initialize dynamic event source manager
        dynamic_source_manager = get_dynamic_source_manager()
        
        # Create event aggregator from stored connections (live data only)
        event_aggregator = dynamic_source_manager.create_aggregator()
        logger.info("Event aggregator initialized with dynamic sources (Live Mode)")
        
        # Log source status
        source_status = dynamic_source_manager.get_source_status()
        logger.info(f"Active event sources: {source_status['total_sources']}")
        
        # Initialize compliance tracker
        tracker = get_tracker()
        
        # Load controls from vector store and register with tracker
        controls = vector_store.get_all_controls() if vector_store else []
        if controls:
            tracker.register_controls(controls)
            logger.info(f"Compliance tracker initialized with {len(controls)} controls")
        else:
            logger.info("Compliance tracker initialized (no controls loaded)")
        
        # Initialize skill-based detection system
        detection_system = get_detection_system()
        logger.info("Skill-based detection system created")
        
        # Start monitoring task
        monitoring_task = asyncio.create_task(continuous_monitoring())
        logger.info("Continuous monitoring started")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global monitoring_task, event_aggregator
    
    logger.info("Shutting down...")
    
    if event_aggregator:
        event_aggregator.stop()
    
    if monitoring_task:
        monitoring_task.cancel()
        try:
            await monitoring_task
        except asyncio.CancelledError:
            pass


@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "mock_mode": config.mock_mode if config else True,  # Only affects dashboard fallback data
        "services": {
            "extractor": extractor is not None,
            "vector_store": vector_store is not None,
            "notifications": notification_service is not None,
            "event_aggregator": event_aggregator is not None,
            "tracker": tracker is not None
        }
    }


@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload compliance PDF and extract controls
    
    Args:
        file: PDF file containing compliance controls
        
    Returns:
        Upload response with extracted controls info
    """
    try:
        logger.info(f"Uploading file: {file.filename}")
        
        # Read file content
        content = await file.read()
        
        # Save PDF to storage directory
        pdf_path = PDF_STORAGE_DIR / file.filename
        with open(pdf_path, "wb") as f:
            f.write(content)
        logger.info(f"Saved PDF to {pdf_path}")
        
        # Extract controls
        controls = extractor.extract_from_pdf_bytes(content)
        
        if not controls:
            raise HTTPException(status_code=400, detail="No controls extracted from PDF")
        
        # Build vector store
        vector_store.build_from_controls(controls)
        
        # Register controls with tracker
        tracker.register_controls(controls)
        
        # Initialize/reload detection system with new controls (broadcast new skills)
        if detection_system:
            await detection_system.reload_controls(controls, broadcast_new_skills=True)
            logger.info("Detection system reloaded with new controls")
        
        # Get unique standards
        standards = list(set(c.get('standard', 'Unknown') for c in controls))
        
        logger.info(f"Extracted {len(controls)} controls from {file.filename}")
        
        return {
            "success": True,
            "message": f"Successfully extracted {len(controls)} controls from {file.filename}",
            "controls_count": len(controls),
            "standards": standards,
            "filename": file.filename,
            "saved_path": str(pdf_path)
        }
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-url")
async def upload_pdf_url(url: str):
    """
    Upload compliance PDF from URL
    
    Args:
        url: URL to PDF document
        
    Returns:
        Upload response
    """
    try:
        logger.info(f"Uploading from URL: {url}")
        
        # Extract controls from URL
        controls = extractor.extract_from_url(url)
        
        if not controls:
            raise HTTPException(status_code=400, detail="No controls extracted from URL")
        
        # Build vector store
        vector_store.build_from_controls(controls)
        
        # Register controls with tracker
        tracker.register_controls(controls)
        
        # Initialize/reload detection system with new controls
        if detection_system:
            await detection_system.reload_controls(controls)
            logger.info("Detection system reloaded with new controls")
        
        # Get unique standards
        standards = list(set(c.get('standard', 'Unknown') for c in controls))
        
        return {
            "success": True,
            "message": f"Successfully extracted {len(controls)} controls",
            "controls_count": len(controls),
            "standards": standards
        }
        
    except Exception as e:
        logger.error(f"Error uploading from URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest")
async def ingest_all_pdfs():
    """
    Re-ingest all PDFs from storage directory
    
    Returns:
        Ingestion status with counts
    """
    try:
        logger.info("Starting re-ingestion of all PDFs")
        
        # Get all PDF files from storage
        pdf_files = list(PDF_STORAGE_DIR.glob("*.pdf"))
        
        if not pdf_files:
            return {
                "success": True,
                "message": "No PDFs found in storage directory",
                "files_processed": 0,
                "total_controls": 0
            }
        
        all_controls = []
        processed_files = []
        
        # Process each PDF
        for pdf_path in pdf_files:
            try:
                logger.info(f"Processing {pdf_path.name}")
                
                # Read PDF content
                with open(pdf_path, "rb") as f:
                    content = f.read()
                
                # Extract controls
                controls = extractor.extract_from_pdf_bytes(content)
                
                if controls:
                    all_controls.extend(controls)
                    processed_files.append(pdf_path.name)
                    logger.info(f"Extracted {len(controls)} controls from {pdf_path.name}")
                else:
                    logger.warning(f"No controls extracted from {pdf_path.name}")
                    
            except Exception as e:
                logger.error(f"Error processing {pdf_path.name}: {e}")
                continue
        
        if all_controls:
            # Rebuild vector store with all controls
            vector_store.build_from_controls(all_controls)
            
            # Re-register controls with tracker
            tracker.register_controls(all_controls)
            
            logger.info(f"Re-ingestion complete: {len(processed_files)} files, {len(all_controls)} controls")
        
        return {
            "success": True,
            "message": f"Successfully re-ingested {len(processed_files)} PDFs",
            "files_processed": len(processed_files),
            "total_controls": len(all_controls),
            "processed_files": processed_files
        }
        
    except Exception as e:
        logger.error(f"Error during re-ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/{filename}")
async def ingest_single_pdf(filename: str):
    """
    Re-ingest a specific PDF from storage directory
    
    Args:
        filename: Name of the PDF file to ingest
        
    Returns:
        Ingestion status
    """
    try:
        logger.info(f"Starting re-ingestion of {filename}")
        
        # Check if file exists
        pdf_path = PDF_STORAGE_DIR / filename
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail=f"PDF file '{filename}' not found in storage")
        
        # Read PDF content
        with open(pdf_path, "rb") as f:
            content = f.read()
        
        # Extract controls
        controls = extractor.extract_from_pdf_bytes(content)
        
        if not controls:
            raise HTTPException(status_code=400, detail=f"No controls extracted from {filename}")
        
        # Get existing controls and add new ones
        existing_controls = vector_store.get_all_controls()
        
        # Remove old controls from this file (if any) and add new ones
        # Filter out controls from this file based on metadata
        filtered_controls = [c for c in existing_controls if c.get('source_file') != filename]
        
        # Add source file metadata to new controls
        for control in controls:
            control['source_file'] = filename
        
        # Combine and rebuild
        all_controls = filtered_controls + controls
        vector_store.build_from_controls(all_controls)
        
        # Re-register with tracker
        tracker.register_controls(all_controls)
        
        # Initialize/reload detection system
        if detection_system:
            await detection_system.reload_controls(all_controls)
            logger.info("Detection system reloaded after single PDF ingestion")
        
        # Get unique standards
        standards = list(set(c.get('standard', 'Unknown') for c in controls))
        
        logger.info(f"Re-ingested {len(controls)} controls from {filename}")
        
        return {
            "success": True,
            "message": f"Successfully re-ingested {filename}",
            "controls_count": len(controls),
            "standards": standards,
            "filename": filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error re-ingesting {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pdfs")
async def list_stored_pdfs():
    """
    List all PDFs in storage directory
    
    Returns:
        List of stored PDF files with metadata
    """
    try:
        pdf_files = list(PDF_STORAGE_DIR.glob("*.pdf"))
        
        files_info = []
        for pdf_path in pdf_files:
            stat = pdf_path.stat()
            files_info.append({
                "filename": pdf_path.name,
                "size_bytes": stat.st_size,
                "modified_time": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                "path": str(pdf_path)
            })
        
        return {
            "success": True,
            "count": len(files_info),
            "files": files_info
        }
        
    except Exception as e:
        logger.error(f"Error listing PDFs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/skills")
async def get_skills():
    """
    Get all agent skills with their metadata
    
    Returns:
        List of skills with enable/disable state
    """
    try:
        from models.skill import get_skill_persistence
        
        skill_persistence = get_skill_persistence()
        skills = skill_persistence.list_all()
        stats = skill_persistence.get_stats()
        
        return {
            "success": True,
            "skills": [skill.to_dict() for skill in skills],
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error fetching skills: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/skills/{skill_id}/enable")
async def enable_skill(skill_id: str):
    """
    Enable a specific skill
    
    Args:
        skill_id: ID of the skill to enable
        
    Returns:
        Success status
    """
    try:
        from models.skill import get_skill_persistence
        
        skill_persistence = get_skill_persistence()
        success = skill_persistence.enable_skill(skill_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")
        
        # Reload detection system to apply changes
        if detection_system:
            vector_store_instance = get_vector_store()
            controls = []
            if hasattr(vector_store_instance, 'controls_map'):
                controls = list(vector_store_instance.controls_map.values())
            
            if controls:
                await detection_system.reload_controls(controls, broadcast_new_skills=False)
        
        # Broadcast skill state change
        await ws_manager.broadcast({
            'type': 'skill_state_changed',
            'data': {
                'skill_id': skill_id,
                'enabled': True,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        })
        
        return {
            "success": True,
            "message": f"Skill '{skill_id}' enabled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling skill: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/skills/{skill_id}/disable")
async def disable_skill(skill_id: str):
    """
    Disable a specific skill
    
    Args:
        skill_id: ID of the skill to disable
        
    Returns:
        Success status
    """
    try:
        from models.skill import get_skill_persistence
        
        skill_persistence = get_skill_persistence()
        success = skill_persistence.disable_skill(skill_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found")
        
        # Reload detection system to apply changes
        if detection_system:
            vector_store_instance = get_vector_store()
            controls = []
            if hasattr(vector_store_instance, 'controls_map'):
                controls = list(vector_store_instance.controls_map.values())
            
            if controls:
                await detection_system.reload_controls(controls, broadcast_new_skills=False)
        
        # Broadcast skill state change
        await ws_manager.broadcast({
            'type': 'skill_state_changed',
            'data': {
                'skill_id': skill_id,
                'enabled': False,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        })
        
        return {
            "success": True,
            "message": f"Skill '{skill_id}' disabled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling skill: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/controls")
async def get_controls(standard: Optional[str] = None):
    """
    Get all compliance controls from vector store
    
    Args:
        standard: Optional filter by specific standard
        
    Returns:
        List of compliance controls
    """
    try:
        # Get all controls from vector store
        all_controls = vector_store.get_all_controls() if vector_store else []
        
        # Filter by standard if specified
        if standard:
            all_controls = [c for c in all_controls if c.get('standard') == standard]
        
        return {
            "success": True,
            "count": len(all_controls),
            "controls": all_controls
        }
        
    except Exception as e:
        logger.error(f"Error fetching controls: {e}")
        # Return empty list instead of error for better UX
        return {
            "success": True,
            "count": 0,
            "controls": []
        }


@app.get("/compliance-score", response_model=ComplianceScoreResponse)
async def get_compliance_score(standard: Optional[str] = None):
    """
    Get compliance score
    
    Args:
        standard: Optional specific standard
        
    Returns:
        Compliance score data
    """
    try:
        score_data = tracker.get_compliance_score(standard)
        return score_data
    except Exception as e:
        logger.error(f"Error getting compliance score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard")
async def get_dashboard():
    """Get comprehensive dashboard data - uses MOCK_MODE for fallback demo data only"""
    try:
        # Check if mock mode is enabled for dashboard fallback
        # Note: Event sources always use live data; mock_mode only affects dashboard display
        if config.mock_mode:
            # Use mock data service for rich demo data (dashboard display only)
            mock_service = get_mock_data_service()
            
            dashboard_data = {
                "compliance_score": mock_service.get_compliance_scores(live=True),
                "violations": mock_service.get_violations(),
                "cloud_connections": mock_service.get_cloud_event_trackers(),
                "configuration_drift": mock_service._data.get("configuration_drift"),
                "persona_insights": mock_service._data.get("persona_insights"),
                "recent_events": mock_service.get_recent_events(limit=10),
                "security_metrics": mock_service.get_security_metrics(),
                "ibm_cloud_at_events": mock_service._data.get("ibm_cloud_at_events", [])
            }
        else:
            # Use real data from tracker and event sources
            score_data = tracker.get_compliance_score()
            violations_list = tracker.get_all_violations()
            
            # Get cloud connections from connection manager
            from infrastructure.cloud.connection_manager import get_connection_manager
            connection_manager = get_connection_manager()
            connections = connection_manager.list_connections()
            
            # Format connections for dashboard (similar to mock data format)
            cloud_connections = []
            for conn in connections:
                cloud_connections.append({
                    "id": conn.id,
                    "name": conn.name,
                    "provider": conn.provider.value,
                    "status": conn.status.value,
                    "enabled": conn.enabled,
                    "events_processed": conn.events_processed,
                    "last_event_at": conn.last_event_at.isoformat() if conn.last_event_at else None,
                    "error_count": conn.error_count,
                    "last_error": conn.last_error,
                    "created_at": conn.created_at.isoformat() if conn.created_at else None,
                    "updated_at": conn.updated_at.isoformat() if conn.updated_at else None
                })
            
            dashboard_data = {
                "compliance_score": score_data,
                "violations": violations_list,
                "cloud_connections": cloud_connections,
                "recent_events": [],  # Would come from event aggregator
                "security_metrics": {
                    "total_violations": len(violations_list),
                    "critical_violations": len([v for v in violations_list if v.get("severity") == "critical"]),
                    "high_violations": len([v for v in violations_list if v.get("severity") == "high"])
                },
                "persona_insights": None,
                "configuration_drift": None
            }
        
        return dashboard_data
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/violations")
async def get_violations(standard: Optional[str] = None):
    """Get violations by severity and category"""
    try:
        return {
            "by_severity": tracker.get_violations_by_severity(standard),
            "by_category": tracker.get_violations_by_category(standard)
        }
    except Exception as e:
        logger.error(f"Error getting violations: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/violations/details")
async def get_violation_details(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    include_resolved: bool = False
):
    """
    Get detailed violations with filtering from compliance tracker
    
    Args:
        status: Filter by status (resolved/unresolved)
        severity: Filter by severity (critical, high, medium, low)
        include_resolved: Include resolved violations
        
    Returns:
        List of violations with full details
    """
    try:
        # Get violations from tracker
        all_violations = tracker.get_all_violations(include_resolved=include_resolved)
        
        # Apply filters
        filtered_violations = all_violations
        
        if severity:
            filtered_violations = [v for v in filtered_violations if v.get('severity') == severity]
        
        if status == 'resolved':
            filtered_violations = [v for v in filtered_violations if v.get('resolved')]
        elif status == 'unresolved':
            filtered_violations = [v for v in filtered_violations if not v.get('resolved')]
        
        # Sort by timestamp (most recent first)
        filtered_violations.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Calculate stats
        stats = {
            'total': len(filtered_violations),
            'by_severity': {},
            'by_standard': {},
            'by_category': {},
            'resolved': len([v for v in filtered_violations if v.get('resolved')]),
            'unresolved': len([v for v in filtered_violations if not v.get('resolved')])
        }
        
        for v in filtered_violations:
            sev = v.get('severity', 'unknown')
            std = v.get('standard', 'Unknown')
            cat = v.get('category', 'Unknown')
            
            stats['by_severity'][sev] = stats['by_severity'].get(sev, 0) + 1
            stats['by_standard'][std] = stats['by_standard'].get(std, 0) + 1
            stats['by_category'][cat] = stats['by_category'].get(cat, 0) + 1
        
        return {
            "violations": filtered_violations,
            "total": len(filtered_violations),
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting violation details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/violations/{violation_id}")
async def get_violation_by_id(violation_id: str):
    """
    Get a specific violation by ID
    
    Args:
        violation_id: The violation ID
        
    Returns:
        Violation details with root cause analysis and fix steps
    """
    try:
        mock_service = get_mock_data_service()
        violation = mock_service.get_violation_by_id(violation_id)
        
        if not violation:
            raise HTTPException(status_code=404, detail="Violation not found")
        
        return violation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting violation {violation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/security-metrics")
async def get_security_metrics():
    """
    Get security metrics and threat intelligence
    
    Returns:
        Security metrics including threat level, incidents, and vulnerabilities
    """
    try:
        mock_service = get_mock_data_service()
        return mock_service.get_security_metrics()
    except Exception as e:
        logger.error(f"Error getting security metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/compliance-score/live")
async def get_live_compliance_score():
    """
    Get live compliance score with simulation
    
    Returns:
        Compliance score that updates every 30 seconds
    """
    try:
        mock_service = get_mock_data_service()
        scores = mock_service.get_compliance_scores(live=True)
        return {
            "scores": scores,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "simulation_enabled": True
        }
    except Exception as e:
        logger.error(f"Error getting live compliance score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard/{role}")
async def get_dashboard_by_role(role: str):
    """
    Get dashboard data customized for specific role
    
    Args:
        role: User role (admin, user, auditor, security)
        
    Returns:
        Role-specific dashboard data
    """
    try:
        mock_service = get_mock_data_service()
        return mock_service.get_dashboard_data(role=role)
    except Exception as e:
        logger.error(f"Error getting dashboard for role {role}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint moved to line 910 with enhanced functionality

async def continuous_monitoring():
    """Continuous monitoring loop with skill-based detection"""
    logger.info("Starting continuous monitoring loop with skill-based detection")
    
    # Initialize detection system from vector store if not already initialized
    if detection_system and not detection_system.initialized:
        try:
            controls = vector_store.get_all_controls() if vector_store else []
            if controls:
                await detection_system.initialize(controls, broadcast_new_skills=True)
                logger.info(f"Detection system initialized with {len(controls)} controls")
        except Exception as e:
            logger.error(f"Failed to initialize detection system: {e}")
    
    try:
        async for event in event_aggregator.start():
            try:
                # Process event through skill-based detection system
                if detection_system and detection_system.initialized:
                    results = await detection_system.process_event(event)
                    
                    # Log processing results
                    if results.get('violations'):
                        logger.info(
                            f"Skill-based detection found {len(results['violations'])} violations "
                            f"for event {event.get('event_name')}"
                        )
                    
                    # Broadcast event processing status
                    if not results.get('violations'):
                        await ws_manager.broadcast({
                            "type": "event_processed",
                            "event": {
                                "source": event.get('source'),
                                "event_name": event.get('event_name'),
                                "resource_name": event.get('resource_name'),
                                "timestamp": event.get('event_time')
                            },
                            "status": "compliant"
                        })
                else:
                    # Fallback to legacy rule-based detection
                    logger.warning("Detection system not initialized, using legacy detection")
                    controls = vector_store.get_all_controls() if vector_store else []
                    
                    if not controls:
                        continue
                    
                    # Evaluate event against controls
                    violations = evaluate_controls(controls, event)
                    
                    # Process each violation
                    for violation in violations:
                        # Generate evidence
                        evidence = generate_evidence(event, violation)
                        
                        # Record violation
                        tracker.record_violation(violation, event)
                        
                        # Get updated compliance score
                        compliance_score = tracker.get_compliance_score()
                        
                        # Broadcast real-time updates via WebSocket
                        await ws_manager.broadcast({
                            "type": "violation_detected",
                            "violation": {
                                "control_id": violation.get('control_id'),
                                "standard": violation.get('standard'),
                                "severity": violation.get('severity'),
                                "description": violation.get('description'),
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            },
                            "event": {
                                "source": event.get('source'),
                                "event_name": event.get('event_name'),
                                "resource_name": event.get('resource_name'),
                                "resource_type": event.get('resource_type'),
                                "timestamp": event.get('event_time')
                            },
                            "compliance_score": compliance_score
                        })
                        
                        logger.info(f"Processed violation: {violation.get('control_id')} from {event.get('source')}")
                
            except Exception as e:
                logger.error(f"Error processing event: {e}", exc_info=True)
                continue
    
    except asyncio.CancelledError:
        logger.info("Monitoring loop cancelled")
    except Exception as e:
        logger.error(f"Monitoring loop error: {e}", exc_info=True)


# ============================================================================
# PR TRACKING ENDPOINTS
# ============================================================================

@app.get("/prs")
async def get_all_prs(
    status: Optional[str] = None,
    violation_id: Optional[str] = None
):
    """
    Get all PRs with optional filtering
    
    Args:
        status: Filter by status (open, merged, closed)
        violation_id: Filter by violation ID
        
    Returns:
        List of PRs with statistics
    """
    try:
        pr_tracker = get_pr_tracker()
        prs = pr_tracker.get_all_prs(status=status, violation_id=violation_id)
        stats = pr_tracker.get_pr_stats()
        
        return {
            "prs": prs,
            "total": len(prs),
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting PRs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/prs/{pr_id}")
async def get_pr_by_id(pr_id: str):
    """
    Get a specific PR by ID
    
    Args:
        pr_id: PR ID
        
    Returns:
        PR details
    """
    try:
        pr_tracker = get_pr_tracker()
        pr = pr_tracker.get_pr_by_id(pr_id)
        
        if not pr:
            raise HTTPException(status_code=404, detail="PR not found")
        
        return pr
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/violations/{violation_id}/prs")
async def get_prs_for_violation(violation_id: str):
    """
    Get all PRs linked to a specific violation
    
    Args:
        violation_id: Violation ID
        
    Returns:
        List of PRs for the violation
    """
    try:
        pr_tracker = get_pr_tracker()
        prs = pr_tracker.get_prs_for_violation(violation_id)
        
        return {
            "violation_id": violation_id,
            "prs": prs,
            "total": len(prs)
        }
    except Exception as e:
        logger.error(f"Error getting PRs for violation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# SKILL-BASED DETECTION ENDPOINTS
# ============================================================================

@app.get("/skills")
async def get_all_skills(
    category: Optional[str] = None,
    provider: Optional[str] = None
):
    """
    Get all registered skills
    
    Args:
        category: Filter by category (detection, analysis, remediation)
        provider: Filter by provider (ibm_cloud, aws, azure, all)
        
    Returns:
        List of skills with metadata
    """
    try:
        if not detection_system or not detection_system.initialized:
            return {
                "success": False,
                "message": "Detection system not initialized",
                "skills": []
            }
        
        from services.agent_skills import SkillCategory
        
        registry = detection_system.skill_registry
        
        if category:
            try:
                cat_enum = SkillCategory(category.lower())
                skills = registry.list_by_category(cat_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
        elif provider:
            skills = registry.list_by_provider(provider)
        else:
            skills = registry.list_all()
        
        return {
            "success": True,
            "count": len(skills),
            "skills": [skill.to_dict() for skill in skills],
            "stats": registry.get_stats()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting skills: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/skills/stats")
async def get_skill_stats():
    """
    Get skill execution statistics
    
    Returns:
        Statistics about skill execution and detection system
    """
    try:
        if not detection_system:
            return {
                "success": False,
                "message": "Detection system not initialized"
            }
        
        stats = detection_system.get_stats()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting skill stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/detection-system/status")
async def get_detection_system_status():
    """
    Get detection system status
    
    Returns:
        Status of the skill-based detection system
    """
    try:
        if not detection_system:
            return {
                "initialized": False,
                "message": "Detection system not created"
            }
        
        stats = detection_system.get_stats()
        
        return {
            "initialized": detection_system.initialized,
            "events_processed": stats.get('events_processed', 0),
            "violations_detected": stats.get('violations_detected', 0),
            "violation_rate": stats.get('violation_rate', 0),
            "skill_registry": stats.get('skill_registry', {}),
            "agents": {
                "detection": stats.get('detection_agent', {}),
                "analysis": stats.get('analysis_agent', {}),
                "remediation": stats.get('remediation_agent', {})
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting detection system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/detection-system/reload")
async def reload_detection_system():
    """
    Reload detection system with current controls
    
    Returns:
        Reload status
    """
    try:
        if not detection_system:
            raise HTTPException(status_code=500, detail="Detection system not created")
        
        if not vector_store:
            raise HTTPException(status_code=500, detail="Vector store not initialized")
        
        # Get all controls from vector store
        controls = vector_store.get_all_controls()
        
        if not controls:
            return {
                "success": False,
                "message": "No controls found in vector store"
            }
        
        # Reload detection system
        await detection_system.reload_controls(controls)
        
        stats = detection_system.get_stats()
        
        return {
            "success": True,
            "message": f"Detection system reloaded with {len(controls)} controls",
            "controls_count": len(controls),
            "stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reloading detection system: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        logger.error(f"Error getting PRs for violation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class LinkPRRequest(BaseModel):
    pr_url: str
    pr_number: int
    violation_id: str
    title: str
    description: str = ""
    author: str = ""
    repository: str = ""


@app.post("/prs/link")
async def link_pr_to_violation(request: LinkPRRequest):
    """
    Link a PR to a compliance violation
    
    Args:
        request: PR linking request
        
    Returns:
        Created PR record
    """
    try:
        pr_tracker = get_pr_tracker()
        pr = pr_tracker.link_pr_to_violation(
            pr_url=request.pr_url,
            pr_number=request.pr_number,
            violation_id=request.violation_id,
            title=request.title,
            description=request.description,
            author=request.author,
            repository=request.repository
        )
        
        return {
            "success": True,
            "message": f"Successfully linked PR #{request.pr_number} to violation {request.violation_id}",
            "pr": pr
        }
    except Exception as e:
        logger.error(f"Error linking PR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class UpdatePRStatusRequest(BaseModel):
    status: str
    merged_at: Optional[str] = None
    closed_at: Optional[str] = None


@app.put("/prs/{pr_id}/status")
async def update_pr_status(pr_id: str, request: UpdatePRStatusRequest):
    """
    Update PR status
    
    Args:
        pr_id: PR ID
        request: Status update request
        
    Returns:
        Updated PR record
    """
    try:
        pr_tracker = get_pr_tracker()
        pr = pr_tracker.update_pr_status(
            pr_id=pr_id,
            status=request.status,
            merged_at=request.merged_at,
            closed_at=request.closed_at
        )
        
        if not pr:
            raise HTTPException(status_code=404, detail="PR not found")
        
        return {
            "success": True,
            "message": f"Successfully updated PR {pr_id} status to {request.status}",
            "pr": pr
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating PR status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/prs/{pr_id}/verify-fix")
async def verify_pr_fix(pr_id: str):
    """
    Verify if a merged PR fixes the related violation
    
    Args:
        pr_id: PR ID
        
    Returns:
        Verification result
    """
    try:
        pr_tracker = get_pr_tracker()
        result = pr_tracker.verify_fix_on_merge(pr_id)
        
        return result
    except Exception as e:
        logger.error(f"Error verifying PR fix: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pr-stats")
async def get_pr_statistics():
    """
    Get PR statistics
    
    Returns:
        PR statistics
    """
    try:
        pr_tracker = get_pr_tracker()
        stats = pr_tracker.get_pr_stats()
        
        return stats
    except Exception as e:
        logger.error(f"Error getting PR stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WebSocket Endpoints
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, role: str = "guest"):
    """
    WebSocket endpoint for real-time alerts and updates
    
    Query Parameters:
    - role: User role (admin, user, auditor, security, guest)
    
    Message Types Sent:
    - connection: Connection status
    - violation: New violation detected
    - compliance_update: Compliance score updated
    - pr_update: PR status changed
    - remediation: Remediation action taken
    - heartbeat: Periodic keepalive
    """
    await ws_manager.connect(websocket, role)
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            
            # Handle client messages (ping, subscribe, etc.)
            try:
                message = json.loads(data)
                msg_type = message.get("type")
                
                if msg_type == "ping":
                    await ws_manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }, websocket)
                    
                elif msg_type == "subscribe":
                    # Handle subscription to specific event types
                    await ws_manager.send_personal_message({
                        "type": "subscribed",
                        "events": message.get("events", []),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }, websocket)
                    
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from WebSocket: {data}")
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        ws_manager.disconnect(websocket)


@app.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    return {
        "total_connections": ws_manager.get_connection_count(),
        "connections_by_role": {
            "admin": ws_manager.get_connections_by_role("admin"),
            "user": ws_manager.get_connections_by_role("user"),
            "auditor": ws_manager.get_connections_by_role("auditor"),
            "security": ws_manager.get_connections_by_role("security"),
            "guest": ws_manager.get_connections_by_role("guest")
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/ws/broadcast/violation")
async def broadcast_violation_alert(violation: dict):
    """
    Manually broadcast a violation alert to all connected clients
    (For testing or manual triggers)
    """
    try:
        await ws_manager.broadcast_violation(violation)
        return {"success": True, "message": "Violation broadcasted"}
    except Exception as e:
        logger.error(f"Error broadcasting violation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ws/broadcast/compliance")
async def broadcast_compliance_update(compliance_data: dict):
    """
    Manually broadcast a compliance update to all connected clients
    (For testing or manual triggers)
    """
    try:
        await ws_manager.broadcast_compliance_update(compliance_data)
        return {"success": True, "message": "Compliance update broadcasted"}
    except Exception as e:
        logger.error(f"Error broadcasting compliance update: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# REPORT GENERATION ENDPOINTS
# ============================================================================

class GenerateReportRequest(BaseModel):
    report_type: str = "compliance"
    standard: Optional[str] = None
    format: str = "json"


@app.post("/reports/generate")
async def generate_report(request: GenerateReportRequest):
    """
    Generate a compliance audit report
    
    Args:
        request: Report generation request
        
    Returns:
        Report metadata including download path
    """
    try:
        from services.report_generator import get_report_generator
        
        report_gen = get_report_generator()
        mock_service = get_mock_data_service()
        
        # Get data for report
        compliance_data = mock_service.get_compliance_scores(live=True)
        violations = mock_service.get_violations()
        
        # Build audit trail
        pr_tracker = get_pr_tracker()
        prs = pr_tracker.get_all_prs()
        audit_trail = []
        
        for violation in violations:
            audit_trail.append({
                'id': f"{violation['id']}-detected",
                'violation_id': violation['id'],
                'control_id': violation['control_id'],
                'event_type': 'detected',
                'timestamp': violation['timestamp'],
                'details': f"Violation detected: {violation['description']}"
            })
        
        # Generate report
        report = report_gen.generate_report(
            report_type=request.report_type,
            standard=request.standard,
            format=request.format,
            compliance_data=compliance_data,
            violations=violations,
            audit_trail=audit_trail
        )
        
        return {
            "success": True,
            "message": "Report generated successfully",
            "report": report
        }
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports")
async def list_reports(
    standard: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
):
    """
    List all generated reports with optional filtering
    
    Args:
        standard: Filter by standard
        status: Filter by status
        limit: Maximum number of reports
        
    Returns:
        List of report metadata
    """
    try:
        from services.report_generator import get_report_generator
        
        report_gen = get_report_generator()
        reports = report_gen.list_reports(standard=standard, status=status, limit=limit)
        
        return {
            "success": True,
            "reports": reports,
            "total": len(reports)
        }
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports/{report_id}")
async def get_report(report_id: str):
    """
    Get report metadata by ID
    
    Args:
        report_id: Report ID
        
    Returns:
        Report metadata
    """
    try:
        from services.report_generator import get_report_generator
        
        report_gen = get_report_generator()
        report = report_gen.get_report(report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports/{report_id}/download")
async def download_report(report_id: str):
    """
    Download a generated report file
    
    Args:
        report_id: Report ID
        
    Returns:
        Report file
    """
    try:
        from services.report_generator import get_report_generator
        from fastapi.responses import FileResponse
        
        report_gen = get_report_generator()
        report = report_gen.get_report(report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        file_path = Path(report['file_path'])
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Report file not found")
        
        return FileResponse(
            path=str(file_path),
            filename=file_path.name,
            media_type='application/octet-stream'
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/reports/{report_id}")
async def delete_report(report_id: str):
    """
    Delete a report
    
    Args:
        report_id: Report ID
        
    Returns:
        Deletion status
    """
    try:
        from services.report_generator import get_report_generator
        
        report_gen = get_report_generator()
        success = report_gen.delete_report(report_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return {
            "success": True,
            "message": f"Report {report_id} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# EVIDENCE MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/evidence/violations/{violation_id}")
async def get_evidence_for_violation(violation_id: str):
    """
    Get all evidence for a specific violation
    
    Args:
        violation_id: Violation ID
        
    Returns:
        List of evidence metadata
    """
    try:
        from services.evidence_manager import get_evidence_manager
        
        evidence_mgr = get_evidence_manager()
        evidence = evidence_mgr.get_evidence_by_violation(violation_id)
        
        return {
            "success": True,
            "violation_id": violation_id,
            "evidence": evidence,
            "total": len(evidence)
        }
    except Exception as e:
        logger.error(f"Error getting evidence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/evidence/{evidence_id}")
async def get_evidence(evidence_id: str):
    """
    Get evidence metadata by ID
    
    Args:
        evidence_id: Evidence ID
        
    Returns:
        Evidence metadata
    """
    try:
        from services.evidence_manager import get_evidence_manager
        
        evidence_mgr = get_evidence_manager()
        evidence = evidence_mgr.get_evidence(evidence_id)
        
        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence not found")
        
        return evidence
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting evidence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/evidence/{evidence_id}/verify")
async def verify_evidence(evidence_id: str, verified_by: str = "auditor"):
    """
    Verify evidence integrity and mark as verified
    
    Args:
        evidence_id: Evidence ID
        verified_by: User who verified the evidence
        
    Returns:
        Verification status
    """
    try:
        from services.evidence_manager import get_evidence_manager
        
        evidence_mgr = get_evidence_manager()
        success = evidence_mgr.verify_evidence(evidence_id, verified_by)
        
        if not success:
            raise HTTPException(status_code=400, detail="Evidence verification failed")
        
        return {
            "success": True,
            "message": f"Evidence {evidence_id} verified successfully",
            "verified_by": verified_by
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying evidence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/evidence/summary")
async def get_evidence_summary():
    """
    Get summary of evidence storage
    
    Returns:
        Evidence storage summary
    """
    try:
        from services.evidence_manager import get_evidence_manager
        
        evidence_mgr = get_evidence_manager()
        summary = evidence_mgr.get_evidence_summary()
        
        return {
            "success": True,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error getting evidence summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=True
    )

# Made with Bob
