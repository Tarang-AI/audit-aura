"""
Test script for skill-based detection agent
Tests the detection system with mock events
"""
import asyncio
import logging
from datetime import datetime, timezone
import pytest

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_detection_agent():
    """Test the skill-based detection agent"""
    
    # Import services
    import sys
    sys.path.insert(0, 'backend')
    
    from services.skill_based_detection_agent import get_detection_system
    from services.vector_store import get_vector_store
    from config import get_config
    
    logger.info("=" * 80)
    logger.info("Testing Skill-Based Detection Agent")
    logger.info("=" * 80)
    
    # Initialize config
    config = get_config()
    logger.info(f"Config loaded - Mock Mode: {config.mock_mode}")
    
    # Initialize vector store
    vector_store = get_vector_store()
    vector_store.initialize(config.openai_api_key)
    logger.info("Vector store initialized")
    
    # Create sample compliance controls
    sample_controls = [
        {
            'control_id': 'TEST-001',
            'description': 'S3 buckets must not be publicly accessible',
            'condition': 'event.public == False',
            'severity': 'critical',
            'remediation': 'Update bucket policy to restrict public access. Remove public ACLs.',
            'category': 'Access Control',
            'standard': 'SOC2',
            'provider': 'aws'
        },
        {
            'control_id': 'TEST-002',
            'description': 'Storage resources must have encryption enabled',
            'condition': 'event.encryption_enabled == True',
            'severity': 'high',
            'remediation': 'Enable encryption at rest using cloud provider key management service.',
            'category': 'Data Protection',
            'standard': 'SOC2',
            'provider': 'all'
        },
        {
            'control_id': 'TEST-003',
            'description': 'Databases must have backup enabled',
            'condition': 'event.backup_enabled == True',
            'severity': 'medium',
            'remediation': 'Enable automated backups with appropriate retention period.',
            'category': 'Business Continuity',
            'standard': 'ISO27001',
            'provider': 'all'
        },
        {
            'control_id': 'TEST-004',
            'description': 'Security groups must not allow all traffic',
            'condition': 'event.allows_all_traffic == False',
            'severity': 'high',
            'remediation': 'Restrict security group rules to specific IP ranges and ports.',
            'category': 'Network Security',
            'standard': 'SOC2',
            'provider': 'aws'
        }
    ]
    
    # Build vector store with controls
    vector_store.build_from_controls(sample_controls)
    logger.info(f"Vector store built with {len(sample_controls)} controls")
    
    # Initialize detection system
    detection_system = get_detection_system()
    await detection_system.initialize(sample_controls)
    logger.info("Detection system initialized")
    
    # Get initial stats
    stats = detection_system.get_stats()
    logger.info(f"Detection system stats: {stats}")
    
    # Create test events
    test_events = [
        {
            'source': 'aws',
            'event_name': 'PutBucketPolicy',
            'event_time': datetime.now(timezone.utc).isoformat(),
            'resource_type': 's3_bucket',
            'resource_name': 'test-bucket-public',
            'public': True,  # VIOLATION
            'encryption_enabled': True,
            'username': 'test-user'
        },
        {
            'source': 'aws',
            'event_name': 'CreateBucket',
            'event_time': datetime.now(timezone.utc).isoformat(),
            'resource_type': 's3_bucket',
            'resource_name': 'test-bucket-unencrypted',
            'public': False,
            'encryption_enabled': False,  # VIOLATION
            'username': 'test-user'
        },
        {
            'source': 'aws',
            'event_name': 'ModifyDBInstance',
            'event_time': datetime.now(timezone.utc).isoformat(),
            'resource_type': 'rds_instance',
            'resource_name': 'test-db-no-backup',
            'public': False,
            'backup_enabled': False,  # VIOLATION
            'multi_az': True,
            'username': 'test-user'
        },
        {
            'source': 'aws',
            'event_name': 'AuthorizeSecurityGroupIngress',
            'event_time': datetime.now(timezone.utc).isoformat(),
            'resource_type': 'security_group',
            'resource_name': 'test-sg-open',
            'allows_all_traffic': True,  # VIOLATION
            'port': 22,
            'username': 'test-user'
        },
        {
            'source': 'aws',
            'event_name': 'CreateBucket',
            'event_time': datetime.now(timezone.utc).isoformat(),
            'resource_type': 's3_bucket',
            'resource_name': 'test-bucket-compliant',
            'public': False,
            'encryption_enabled': True,
            'versioning_enabled': True,
            'username': 'test-user'
        }
    ]
    
    logger.info("\n" + "=" * 80)
    logger.info("Processing Test Events")
    logger.info("=" * 80)
    
    # Process each test event
    for i, event in enumerate(test_events, 1):
        logger.info(f"\n--- Test Event {i}/{len(test_events)} ---")
        logger.info(f"Event: {event['event_name']} on {event['resource_name']}")
        
        # Process event
        results = await detection_system.process_event(event)
        
        # Display results
        if results.get('violations'):
            logger.info(f"✗ VIOLATIONS DETECTED: {len(results['violations'])}")
            for violation in results['violations']:
                logger.info(f"  - Control: {violation.get('control_id')}")
                logger.info(f"    Severity: {violation.get('severity')}")
                logger.info(f"    Description: {violation.get('control_description')}")
        else:
            logger.info("✓ COMPLIANT - No violations detected")
        
        if results.get('analysis'):
            logger.info(f"  Analysis: {len(results['analysis'])} analysis results")
            for analysis in results['analysis']:
                if 'risk_score' in analysis:
                    logger.info(f"    Risk Score: {analysis['risk_score']}/10")
                    logger.info(f"    Priority: {analysis.get('recommended_priority')}")
        
        if results.get('remediation'):
            logger.info(f"  Remediation: {len(results['remediation'])} remediation plans")
    
    # Get final stats
    logger.info("\n" + "=" * 80)
    logger.info("Final Detection System Statistics")
    logger.info("=" * 80)
    
    final_stats = detection_system.get_stats()
    logger.info(f"Events Processed: {final_stats['events_processed']}")
    logger.info(f"Violations Detected: {final_stats['violations_detected']}")
    logger.info(f"Violation Rate: {final_stats['violation_rate']:.2f}%")
    
    if final_stats.get('skill_registry'):
        registry_stats = final_stats['skill_registry']
        logger.info(f"\nSkill Registry:")
        logger.info(f"  Total Skills: {registry_stats['total_skills']}")
        logger.info(f"  By Category: {registry_stats['by_category']}")
        logger.info(f"  By Provider: {registry_stats['by_provider']}")
    
    if final_stats.get('detection_agent'):
        agent_stats = final_stats['detection_agent']
        logger.info(f"\nDetection Agent:")
        logger.info(f"  Total Skills: {agent_stats['total_skills']}")
        logger.info(f"  Total Executions: {agent_stats['total_executions']}")
        logger.info(f"  Success Rate: {agent_stats['success_rate']:.2f}%")
    
    logger.info("\n" + "=" * 80)
    logger.info("Test Complete!")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_detection_agent())