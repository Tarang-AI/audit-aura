"""
Incident Registry for Multi-Agent System
Manages incident tracking in database
"""
import sqlite3
import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Use data directory for incidents database
DB_PATH = "./data/incidents.db"


def get_connection():
    """Returns a SQLite database connection."""
    # Ensure data directory exists
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_registry():
    """Initializes the incident registry database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    create_sql = """
        CREATE TABLE IF NOT EXISTS incidents (
            incident_id VARCHAR(100) PRIMARY KEY,
            status VARCHAR(50),
            severity VARCHAR(50),
            offending_entity VARCHAR(255),
            mapped_controls TEXT,
            incident_ticket_id VARCHAR(100),
            change_ticket_id VARCHAR(100),
            execution_history TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """
    cursor.execute(create_sql)
    conn.commit()
    conn.close()
    logger.info("Incident registry initialized")


def upsert_incident(
    incident_id: str,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    offending_entity: Optional[str] = None,
    mapped_controls: Optional[List[str]] = None,
    incident_ticket_id: Optional[str] = None,
    change_ticket_id: Optional[str] = None,
    execution_history: Optional[List[Dict[str, Any]]] = None
):
    """Inserts or updates an incident in the registry."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if exists
    cursor.execute("SELECT * FROM incidents WHERE incident_id = ?", (incident_id,))
    existing = cursor.fetchone()
    
    now = datetime.now(timezone.utc).isoformat()
    
    if existing:
        fields = []
        values = []
        if status:
            fields.append("status = ?")
            values.append(status)
        if severity:
            fields.append("severity = ?")
            values.append(severity)
        if offending_entity:
            fields.append("offending_entity = ?")
            values.append(offending_entity)
        if mapped_controls:
            fields.append("mapped_controls = ?")
            values.append(json.dumps(mapped_controls))
        if incident_ticket_id:
            fields.append("incident_ticket_id = ?")
            values.append(incident_ticket_id)
        if change_ticket_id:
            fields.append("change_ticket_id = ?")
            values.append(change_ticket_id)
        if execution_history:
            fields.append("execution_history = ?")
            values.append(json.dumps(execution_history))
        
        fields.append("updated_at = ?")
        values.append(now)
        values.append(incident_id)
        
        query = f"UPDATE incidents SET {', '.join(fields)} WHERE incident_id = ?"
        cursor.execute(query, tuple(values))
    else:
        cursor.execute("""
            INSERT INTO incidents (
                incident_id, status, severity, offending_entity, 
                mapped_controls, incident_ticket_id, change_ticket_id, 
                execution_history, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            incident_id, 
            status or "Open", 
            severity or "None", 
            offending_entity or "None",
            json.dumps(mapped_controls or []),
            incident_ticket_id,
            change_ticket_id,
            json.dumps(execution_history or []),
            now,
            now
        ))
    
    conn.commit()
    conn.close()


def get_all_incidents() -> List[Dict[str, Any]]:
    """Retrieves all incidents from the registry."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidents ORDER BY created_at DESC")
    rows = cursor.fetchall()
    
    result = []
    for row in rows:
        d = dict(row)
        d["mapped_controls"] = json.loads(d["mapped_controls"] or "[]")
        d["execution_history"] = json.loads(d["execution_history"] or "[]")
        result.append(d)
        
    conn.close()
    return result


def get_pending_approvals() -> List[Dict[str, Any]]:
    """Retrieves incidents waiting for human approval."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM incidents WHERE status = ? ORDER BY created_at DESC",
        ("Waiting for Approval",)
    )
    rows = cursor.fetchall()
    
    result = []
    for row in rows:
        d = dict(row)
        d["mapped_controls"] = json.loads(d["mapped_controls"] or "[]")
        d["execution_history"] = json.loads(d["execution_history"] or "[]")
        result.append(d)
        
    conn.close()
    return result


def get_stats() -> Dict[str, Any]:
    """Retrieves high-level incident statistics."""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    cursor.execute("SELECT COUNT(*) as count FROM incidents")
    row = cursor.fetchone()
    stats["total_incidents"] = row[0]
    
    cursor.execute("SELECT COUNT(*) as count FROM incidents WHERE severity = ?", ("Critical",))
    row = cursor.fetchone()
    stats["critical_incidents"] = row[0]
    
    cursor.execute("SELECT COUNT(*) as count FROM incidents WHERE status = ?", ("Resolved",))
    row = cursor.fetchone()
    stats["resolved_incidents"] = row[0]
    
    cursor.execute("SELECT COUNT(*) as count FROM incidents WHERE status = ?", ("Waiting for Approval",))
    row = cursor.fetchone()
    stats["pending_approvals"] = row[0]
    
    conn.close()
    return stats


# Initialize registry on module import
try:
    init_registry()
except Exception as e:
    logger.error(f"Failed to initialize incident registry: {e}")

# Made with Bob
