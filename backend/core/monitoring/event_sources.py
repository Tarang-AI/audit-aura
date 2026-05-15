"""
Event Source Integrations
Handles ingestion from CloudWatch, IBM Cloud, and other sources
"""
import logging
import json
from typing import Dict, Any, List, Optional, AsyncIterator
from datetime import datetime, timezone
import asyncio

logger = logging.getLogger(__name__)


class EventSource:
    """Base class for event sources"""
    
    async def get_events(self) -> AsyncIterator[Dict[str, Any]]:
        """Get events from source"""
        raise NotImplementedError


class CloudWatchEventSource(EventSource):
    """AWS CloudWatch event source"""
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        
        try:
            import boto3
            self.client = boto3.client('logs', region_name=region)
            self.cloudtrail = boto3.client('cloudtrail', region_name=region)
            logger.info(f"CloudWatch event source initialized for region {region}")
        except ImportError:
            logger.error("boto3 not installed. Install with: pip install boto3")
            raise
    
    async def get_events(self) -> AsyncIterator[Dict[str, Any]]:
        """Get CloudWatch/CloudTrail events"""
        async for event in self._get_real_events():
            yield event
    
    async def _get_real_events(self) -> AsyncIterator[Dict[str, Any]]:
        """Get real CloudWatch/CloudTrail events"""
        try:
            # Poll for CloudTrail events every 30 seconds
            while True:
                try:
                    # Get CloudTrail events
                    response = self.cloudtrail.lookup_events(MaxResults=50)
                    
                    for event in response.get('Events', []):
                        yield {
                            'source': 'cloudwatch',
                            'event_name': event.get('EventName'),
                            'event_time': event.get('EventTime').isoformat(),
                            'username': event.get('Username'),
                            'resource_type': event.get('ResourceType'),
                            'resource_name': event.get('ResourceName'),
                            'cloud_trail_event': json.loads(event.get('CloudTrailEvent', '{}')),
                            'raw': event
                        }
                    
                    await asyncio.sleep(30)
                    
                except Exception as e:
                    logger.error(f"Error in CloudTrail polling loop: {e}")
                    await asyncio.sleep(30)
                    
        except Exception as e:
            logger.error(f"Error fetching CloudWatch events: {e}")


class IBMCloudEventSource(EventSource):
    """IBM Cloud event source for Activity Tracker, Monitoring, and Logs"""
    
    def __init__(
        self,
        api_key: str,
        region: str = 'us-south',
        activity_tracker_instance_id: Optional[str] = None,
        monitoring_instance_id: Optional[str] = None,
        logs_instance_id: Optional[str] = None
    ):
        if not api_key:
            raise ValueError("IBM Cloud API key is required")
        
        self.api_key = api_key
        self.region = region
        self.activity_tracker_instance_id = activity_tracker_instance_id
        self.monitoring_instance_id = monitoring_instance_id
        self.logs_instance_id = logs_instance_id
        self.client = None
        
        try:
            import requests
            from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
            
            # Initialize IAM authenticator
            self.authenticator = IAMAuthenticator(api_key)
            
            # Get IAM token
            self.token = self._get_iam_token()
            
            if self.token:
                logger.info(f"IBM Cloud authenticated successfully for region {region}")
            else:
                raise ValueError("Failed to get IBM Cloud IAM token")
                
        except ImportError:
            logger.error("IBM Cloud SDK not installed. Install with: pip install ibm-cloud-sdk-core")
            raise
        except Exception as e:
            logger.error(f"IBM Cloud authentication failed: {e}")
            raise
    
    def _get_iam_token(self) -> Optional[str]:
        """Get IBM Cloud IAM token"""
        try:
            import requests
            
            response = requests.post(
                'https://iam.cloud.ibm.com/identity/token',
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                data={
                    'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
                    'apikey': self.api_key
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get('access_token')
            else:
                logger.error(f"Failed to get IAM token: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting IAM token: {e}")
            return None
    
    async def get_events(self) -> AsyncIterator[Dict[str, Any]]:
        """Get IBM Cloud events"""
        async for event in self._get_real_events():
            yield event
    
    async def _get_real_events(self) -> AsyncIterator[Dict[str, Any]]:
        """Get real IBM Cloud Activity Tracker events"""
        import requests
        
        try:
            if not self.token:
                logger.error("No IAM token available")
                return
            
            # Activity Tracker API endpoint
            base_url = f"https://api.{self.region}.logging.cloud.ibm.com"
            
            # Poll for events every 10 seconds
            while True:
                try:
                    # Fetch Activity Tracker events
                    if self.activity_tracker_instance_id:
                        events = await self._fetch_activity_tracker_events(base_url)
                        for event in events:
                            yield event
                    
                    # Fetch Monitoring events
                    if self.monitoring_instance_id:
                        events = await self._fetch_monitoring_events()
                        for event in events:
                            yield event
                    
                    # Fetch Log events
                    if self.logs_instance_id:
                        events = await self._fetch_log_events()
                        for event in events:
                            yield event
                    
                    await asyncio.sleep(10)
                    
                except Exception as e:
                    logger.error(f"Error in event polling loop: {e}")
                    await asyncio.sleep(10)
                    
        except Exception as e:
            logger.error(f"Error fetching IBM Cloud events: {e}")
    
    async def _fetch_activity_tracker_events(self, base_url: str) -> List[Dict[str, Any]]:
        """Fetch events from IBM Cloud Activity Tracker"""
        import requests
        from datetime import datetime, timedelta
        
        try:
            # Query events from last 1 minute
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(minutes=1)
            
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            # Activity Tracker query
            query_url = f"{base_url}/v1/events"
            params = {
                'from': int(start_time.timestamp() * 1000),
                'to': int(end_time.timestamp() * 1000),
                'size': 100
            }
            
            response = requests.get(query_url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                events = data.get('events', [])
                
                # Transform events to our format
                transformed_events = []
                for event in events:
                    transformed_event = {
                        'source': 'ibm_cloud_activity_tracker',
                        'source_instance': f'ibm-at-{self.region}',
                        'event_time': event.get('eventTime', datetime.now(timezone.utc).isoformat()),
                        'event_name': event.get('action', 'unknown'),
                        'action': event.get('action', 'unknown'),
                        'outcome': event.get('outcome', 'unknown'),
                        'initiator': event.get('initiator', {}),
                        'target': event.get('target', {}),
                        'resource_type': event.get('target', {}).get('typeURI', 'unknown'),
                        'resource_name': event.get('target', {}).get('name', 'unknown'),
                        'severity': self._determine_severity(event),
                        'raw': event
                    }
                    transformed_events.append(transformed_event)
                
                return transformed_events
            else:
                logger.warning(f"Activity Tracker API returned {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching Activity Tracker events: {e}")
            return []
    
    async def _fetch_monitoring_events(self) -> List[Dict[str, Any]]:
        """Fetch events from IBM Cloud Monitoring"""
        # Placeholder for IBM Cloud Monitoring integration
        # This would query metrics and alerts from IBM Cloud Monitoring
        return []
    
    async def _fetch_log_events(self) -> List[Dict[str, Any]]:
        """Fetch events from IBM Cloud Logs"""
        # Placeholder for IBM Cloud Logs integration
        # This would query logs from IBM Cloud Logs service
        return []
    
    def _determine_severity(self, event: Dict[str, Any]) -> str:
        """Determine event severity based on action and outcome"""
        action = event.get('action', '').lower()
        outcome = event.get('outcome', '').lower()
        
        # Failed actions are high severity
        if outcome == 'failure':
            return 'high'
        
        # Security-related actions
        if any(keyword in action for keyword in ['delete', 'update', 'modify', 'create']):
            target_type = event.get('target', {}).get('typeURI', '').lower()
            
            # Critical resources
            if any(resource in target_type for resource in ['iam', 'security', 'key', 'policy']):
                return 'critical'
            
            # High priority resources
            if any(resource in target_type for resource in ['bucket', 'database', 'network']):
                return 'high'
            
            return 'medium'
        
        return 'low'


class GenericLogEventSource(EventSource):
    """Generic log file or endpoint event source"""
    
    def __init__(self, endpoint: Optional[str] = None, auth_token: Optional[str] = None):
        self.endpoint = endpoint
        self.auth_token = auth_token
        
        if not endpoint:
            raise ValueError("Generic event source requires an endpoint (file path or URL)")
        
        logger.info(f"Generic event source initialized for endpoint: {endpoint}")
    
    async def get_events(self) -> AsyncIterator[Dict[str, Any]]:
        """Get events from log files or endpoints"""
        async for event in self._get_real_events():
            yield event
    
    async def _get_real_events(self) -> AsyncIterator[Dict[str, Any]]:
        """Read events from log file or endpoint"""
        try:
            # Check if endpoint is a file path or URL
            if self.endpoint.startswith('http://') or self.endpoint.startswith('https://'):
                # HTTP endpoint - poll for events
                async for event in self._poll_http_endpoint():
                    yield event
            else:
                # File path - tail the file
                async for event in self._tail_log_file():
                    yield event
                        
        except Exception as e:
            logger.error(f"Error reading from endpoint {self.endpoint}: {e}")
    
    async def _tail_log_file(self) -> AsyncIterator[Dict[str, Any]]:
        """Tail a log file for new events"""
        import os
        
        if not os.path.exists(self.endpoint):
            logger.error(f"Log file not found: {self.endpoint}")
            return
        
        # Start from end of file
        with open(self.endpoint, 'r') as f:
            # Seek to end
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if line:
                    try:
                        event = json.loads(line)
                        yield event
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in log file: {line}")
                else:
                    # No new data, wait before checking again
                    await asyncio.sleep(1)
    
    async def _poll_http_endpoint(self) -> AsyncIterator[Dict[str, Any]]:
        """Poll an HTTP endpoint for events"""
        import requests
        
        headers = {}
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
        
        while True:
            try:
                response = requests.get(self.endpoint, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Handle different response formats
                    if isinstance(data, list):
                        for event in data:
                            yield event
                    elif isinstance(data, dict):
                        # Single event or wrapped response
                        events = data.get('events', [data])
                        for event in events:
                            yield event
                else:
                    logger.warning(f"HTTP endpoint returned {response.status_code}: {response.text}")
                
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Error polling HTTP endpoint: {e}")
                await asyncio.sleep(10)


class EventAggregator:
    """Aggregates events from multiple sources"""
    
    def __init__(self, sources: List[EventSource]):
        self.sources = sources
        self.running = False
    
    async def start(self) -> AsyncIterator[Dict[str, Any]]:
        """Start aggregating events from all sources"""
        self.running = True
        
        # Use a queue to collect events from all sources
        queue = asyncio.Queue()
        
        async def collect_events(source: EventSource):
            async for event in source.get_events():
                if not self.running:
                    break
                await queue.put(event)
        
        # Start collection tasks
        collection_tasks = [
            asyncio.create_task(collect_events(source))
            for source in self.sources
        ]
        
        # Yield events from queue
        try:
            while self.running:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield event
                except asyncio.TimeoutError:
                    continue
        finally:
            # Cleanup
            for task in collection_tasks:
                task.cancel()
    
    async def _process_source(self, source: EventSource, queue: asyncio.Queue):
        """Process events from a single source and put them in queue"""
        try:
            async for event in source.get_events():
                if not self.running:
                    break
                await queue.put(event)
        except Exception as e:
            logger.error(f"Error processing source: {e}")
    
    def stop(self):
        """Stop aggregating events"""
        self.running = False


def create_event_aggregator(
    ibm_cloud_api_key: Optional[str] = None,
    ibm_cloud_region: str = 'us-south',
    ibm_activity_tracker_instance_id: Optional[str] = None,
    ibm_monitoring_instance_id: Optional[str] = None,
    ibm_logs_instance_id: Optional[str] = None
) -> EventAggregator:
    """
    Create an event aggregator with all configured sources.
    
    Note: This function is deprecated. Use DynamicEventSourceManager instead,
    which creates sources from stored cloud connections.
    """
    logger.warning(
        "create_event_aggregator() is deprecated. "
        "Use DynamicEventSourceManager for production deployments."
    )
    
    sources = []
    
    # Only add IBM Cloud source if API key is provided
    if ibm_cloud_api_key:
        try:
            sources.append(IBMCloudEventSource(
                api_key=ibm_cloud_api_key,
                region=ibm_cloud_region,
                activity_tracker_instance_id=ibm_activity_tracker_instance_id,
                monitoring_instance_id=ibm_monitoring_instance_id,
                logs_instance_id=ibm_logs_instance_id
            ))
        except Exception as e:
            logger.error(f"Failed to create IBM Cloud source: {e}")
    
    if not sources:
        logger.warning(
            "No event sources configured. Please add cloud connections via "
            "the Admin → Connections interface or provide credentials."
        )
    
    return EventAggregator(sources)

# Made with Bob
