"""
Dynamic Event Sources
Creates event sources dynamically from stored connections
"""
import logging
import asyncio
from typing import Dict, List, Optional, AsyncIterator, Any
from datetime import datetime, timezone

from infrastructure.cloud.connection_manager import get_connection_manager
from core.monitoring.event_sources import (
    CloudWatchEventSource,
    IBMCloudEventSource,
    GenericLogEventSource,
    EventAggregator
)
from models.cloud_connection import CloudProvider

logger = logging.getLogger(__name__)


class DynamicEventSourceManager:
    """Manages event sources dynamically based on stored connections"""
    
    def __init__(self):
        self.connection_manager = get_connection_manager()
        self.active_sources: Dict[str, Any] = {}
        self.aggregator: Optional[EventAggregator] = None
        logger.info("Dynamic event source manager initialized")
    
    def create_event_source_from_connection(self, connection_id: str) -> Optional[Any]:
        """
        Create an event source from a connection
        
        Args:
            connection_id: Connection ID
            
        Returns:
            Event source instance or None if failed
        """
        try:
            # Get connection
            connection = self.connection_manager.get_connection(connection_id)
            if not connection or not connection.enabled:
                return None
            
            # Get decrypted config
            config = self.connection_manager.get_decrypted_config(connection_id)
            
            # Create event source based on provider
            if connection.provider == CloudProvider.AWS:
                return self._create_aws_source(config)
            elif connection.provider == CloudProvider.IBM_CLOUD:
                return self._create_ibm_cloud_source(config)
            elif connection.provider == CloudProvider.GENERIC:
                return self._create_generic_source(config)
            else:
                logger.warning(f"Unsupported provider: {connection.provider}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create event source for {connection_id}: {e}")
            return None
    
    def _create_aws_source(self, config: Dict[str, Any]) -> Optional[CloudWatchEventSource]:
        """Create AWS CloudWatch event source"""
        # Check if CloudTrail is enabled
        if not config.get('cloudtrail_enabled', True):
            logger.info("CloudTrail event source is disabled for this connection")
            return None
        
        import boto3
        
        # Create boto3 session with credentials
        session = boto3.Session(
            aws_access_key_id=config.get('access_key_id'),
            aws_secret_access_key=config.get('secret_access_key'),
            aws_session_token=config.get('session_token'),
            region_name=config.get('region', 'us-east-1')
        )
        
        # Create event source with real credentials
        source = CloudWatchEventSource(
            region=config.get('region', 'us-east-1')
        )
        
        # Override client with authenticated session
        source.client = session.client('logs', region_name=config.get('region', 'us-east-1'))
        source.cloudtrail = session.client('cloudtrail', region_name=config.get('region', 'us-east-1'))
        
        # Store CloudTrail configuration
        source.cloudtrail_log_group = config.get('cloudtrail_log_group')
        source.cloudtrail_s3_bucket = config.get('cloudtrail_s3_bucket')
        
        logger.info(f"Created AWS CloudTrail source for region {config.get('region')}")
        return source
    
    def _create_ibm_cloud_source(self, config: Dict[str, Any]) -> Optional[IBMCloudEventSource]:
        """Create IBM Cloud event source"""
        # Check which event sources are enabled
        activity_tracker_enabled = config.get('activity_tracker_enabled', True)
        platform_logs_enabled = config.get('platform_logs_enabled', False)
        monitoring_enabled = config.get('monitoring_enabled', False)
        
        # If no sources are enabled, return None
        if not (activity_tracker_enabled or platform_logs_enabled or monitoring_enabled):
            logger.info("No IBM Cloud event sources are enabled for this connection")
            return None
        
        # Validate API key
        api_key = config.get('api_key')
        if not api_key:
            logger.error("IBM Cloud API key is required but not provided")
            return None
        
        # Create source with enabled services
        source = IBMCloudEventSource(
            api_key=api_key,
            region=config.get('region', 'us-south'),
            activity_tracker_instance_id=config.get('activity_tracker_instance_id') if activity_tracker_enabled else None,
            monitoring_instance_id=config.get('monitoring_instance_id') if monitoring_enabled else None,
            logs_instance_id=config.get('logs_instance_id') if platform_logs_enabled else None
        )
        
        enabled_sources = []
        if activity_tracker_enabled:
            enabled_sources.append('Activity Tracker')
        if platform_logs_enabled:
            enabled_sources.append('Platform Logs')
        if monitoring_enabled:
            enabled_sources.append('Monitoring')
        
        logger.info(f"Created IBM Cloud source for region {config.get('region')} with sources: {', '.join(enabled_sources)}")
        return source
    
    def _create_generic_source(self, config: Dict[str, Any]) -> Optional[GenericLogEventSource]:
        """Create generic log event source"""
        # Generic sources require custom implementation based on config
        # Return None if not properly configured
        log_endpoint = config.get('log_endpoint')
        if not log_endpoint:
            logger.warning("Generic source requires 'log_endpoint' in configuration")
            return None
        
        source = GenericLogEventSource(
            endpoint=log_endpoint,
            auth_token=config.get('auth_token')
        )
        logger.info(f"Created generic event source for endpoint: {log_endpoint}")
        return source
    
    def load_all_sources(self) -> List[Any]:
        """
        Load all event sources from enabled connections
        
        Returns:
            List of event source instances
        """
        sources = []
        
        try:
            # Get all enabled connections
            connections = self.connection_manager.list_connections(enabled_only=True)
            
            logger.info(f"Loading event sources from {len(connections)} enabled connections")
            
            for connection in connections:
                try:
                    source = self.create_event_source_from_connection(connection.id)
                    if source:
                        sources.append(source)
                        self.active_sources[connection.id] = source
                        logger.info(f"Loaded event source: {connection.name} ({connection.provider})")
                except Exception as e:
                    logger.error(f"Failed to load source for {connection.name}: {e}")
                    # Update connection error stats
                    self.connection_manager.update_connection_stats(
                        connection.id,
                        error=str(e)
                    )
            
            logger.info(f"Successfully loaded {len(sources)} event sources")
            
        except Exception as e:
            logger.error(f"Failed to load event sources: {e}")
        
        return sources
    
    def create_aggregator(self) -> EventAggregator:
        """
        Create an event aggregator with all enabled sources
        
        Returns:
            Event aggregator instance
        """
        sources = self.load_all_sources()
        
        # Only use real cloud connections - no mock data
        if len(sources) == 0:
            logger.warning(
                "No event sources available. Please configure cloud connections in Admin → Connections. "
                "The system will not generate any events until real connections are added."
            )
        
        self.aggregator = EventAggregator(sources)
        logger.info(f"Created event aggregator with {len(sources)} live source(s)")
        
        return self.aggregator
    
    async def start_monitoring(self, callback=None) -> AsyncIterator[Dict[str, Any]]:
        """
        Start monitoring events from all sources
        
        Args:
            callback: Optional callback function for each event
            
        Yields:
            Events from all sources
        """
        if not self.aggregator:
            self.create_aggregator()
        
        if not self.aggregator:
            logger.error("Failed to create event aggregator")
            return
        
        logger.info("Starting event monitoring")
        
        async for event in self.aggregator.start():
            # Update connection stats
            source_id = event.get('source_instance') or event.get('source')
            
            # Find connection by source
            for conn_id, source in self.active_sources.items():
                # Update stats for the connection
                self.connection_manager.update_connection_stats(
                    conn_id,
                    events_processed=1,
                    last_event_at=datetime.now(timezone.utc)
                )
                break
            
            # Call callback if provided
            if callback:
                try:
                    await callback(event)
                except Exception as e:
                    logger.error(f"Error in event callback: {e}")
            
            yield event
    
    def stop_monitoring(self):
        """Stop monitoring events"""
        if self.aggregator:
            self.aggregator.stop()
            logger.info("Stopped event monitoring")
    
    def reload_sources(self):
        """Reload all event sources from connections"""
        logger.info("Reloading event sources")
        
        # Stop current aggregator
        if self.aggregator:
            self.aggregator.stop()
        
        # Clear active sources
        self.active_sources.clear()
        
        # Create new aggregator with live sources only
        self.create_aggregator()
        
        logger.info("Event sources reloaded")
    
    def get_source_status(self) -> Dict[str, Any]:
        """
        Get status of all active sources
        
        Returns:
            Dictionary with source status information
        """
        status = {
            'total_sources': len(self.active_sources),
            'sources': []
        }
        
        for conn_id in self.active_sources.keys():
            connection = self.connection_manager.get_connection(conn_id)
            if connection:
                status['sources'].append({
                    'connection_id': conn_id,
                    'name': connection.name,
                    'provider': connection.provider,
                    'status': connection.status,
                    'events_processed': connection.events_processed,
                    'last_event_at': connection.last_event_at.isoformat() if connection.last_event_at else None,
                    'error_count': connection.error_count
                })
        
        return status


# Global dynamic event source manager instance
_dynamic_source_manager: Optional[DynamicEventSourceManager] = None


def get_dynamic_source_manager() -> DynamicEventSourceManager:
    """Get the global dynamic event source manager instance"""
    global _dynamic_source_manager
    if _dynamic_source_manager is None:
        _dynamic_source_manager = DynamicEventSourceManager()
    return _dynamic_source_manager


# Made with Bob