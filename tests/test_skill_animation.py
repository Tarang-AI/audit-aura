#!/usr/bin/env python3
"""
Test script to verify skill acquisition animation
Simulates the backend broadcasting skills_acquired message
"""
import asyncio
import json
from datetime import datetime, timezone
import pytest

@pytest.mark.asyncio
async def test_skill_broadcast():
    """Test broadcasting skills acquired message"""
    try:
        # Import WebSocket manager
        from infrastructure.messaging.websocket import ws_manager
        
        # Sample skills data
        test_skills = [
            {
                "skill_id": "detect_soc2_cc6_1",
                "name": "Detect Public S3 Bucket Access",
                "description": "Monitors S3 buckets for public access violations",
                "category": "detection",
                "control_id": "CC6.1",
                "standard": "SOC2",
                "severity": "high"
            },
            {
                "skill_id": "detect_hipaa_164_312",
                "name": "Detect Unencrypted Data Storage",
                "description": "Monitors for unencrypted data storage violations",
                "category": "detection",
                "control_id": "164.312",
                "standard": "HIPAA",
                "severity": "critical"
            },
            {
                "skill_id": "analyze_security_impact",
                "name": "Security Impact Analysis",
                "description": "Analyzes the security impact of detected violations",
                "category": "analysis",
                "severity": "medium"
            }
        ]
        
        # Create skills_acquired message
        message = {
            'type': 'skills_acquired',
            'data': {
                'skills': test_skills,
                'count': len(test_skills),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        }
        
        print("Broadcasting skills_acquired message...")
        print(json.dumps(message, indent=2))
        
        # Broadcast to all connected WebSocket clients
        await ws_manager.broadcast(message)
        
        print("\n✅ Skills acquired message broadcasted successfully!")
        print(f"   Broadcasted {len(test_skills)} skills")
        print("\nIf frontend is connected, the animation should now appear.")
        
    except Exception as e:
        print(f"❌ Error broadcasting skills: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("Skill Acquisition Animation Test")
    print("=" * 60)
    print("\nThis script tests the skill acquisition animation by")
    print("broadcasting a skills_acquired message via WebSocket.")
    print("\nMake sure:")
    print("1. Backend server is running (python backend/main.py)")
    print("2. Frontend is running (npm run dev)")
    print("3. Frontend is connected to WebSocket")
    print("\n" + "=" * 60 + "\n")
    
    asyncio.run(test_skill_broadcast())