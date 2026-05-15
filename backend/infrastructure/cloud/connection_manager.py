"""
Cloud Connection Manager
Manages cloud provider connections with secure credential storage
"""
import json
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pathlib import Path

from models.cloud_connection import (
    CloudConnection,
    CloudConnectionCreate,
    CloudConnectionUpdate,
    CloudConnectionResponse,
    CloudProvider,
    ConnectionStatus,
    ConnectionTestResponse
)
from infrastructure.security.encryption import get_encryption_service
from core.monitoring.event_sources import (
    CloudWatchEventSource,
    IBMCloudEventSource,
    GenericLogEventSource
)

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages cloud provider connections"""
    
    def __init__(self, storage_path: str = "./data/connections.json"):
        """
        Initialize connection manager
        
        Args:
            storage_path: Path to store connection data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.encryption_service = get_encryption_service()
        self.connections: Dict[str, CloudConnection] = {}
        self._load_connections()
        logger.info(f"Connection manager initialized with {len(self.connections)} connections")
    
    def _load_connections(self):
        """Load connections from storage"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    for conn_data in data.get('connections', []):
                        connection = CloudConnection(**conn_data)
                        self.connections[connection.id] = connection
                logger.info(f"Loaded {len(self.connections)} connections from storage")
        except Exception as e:
            logger.error(f"Failed to load connections: {e}")
            self.connections = {}
    
    def _save_connections(self):
        """Save connections to storage"""
        try:
            data = {
                'connections': [
                    conn.dict() for conn in self.connections.values()
                ],
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Saved {len(self.connections)} connections to storage")
        except Exception as e:
            logger.error(f"Failed to save connections: {e}")
            raise
    
    def create_connection(self, connection_data: CloudConnectionCreate) -> CloudConnectionResponse:
        """
        Create a new cloud connection
        
        Args:
            connection_data: Connection creation data
            
        Returns:
            Created connection response
        """
        try:
            # Generate unique ID
            connection_id = str(uuid.uuid4())
            
            # Encrypt configuration
            encrypted_config = self.encryption_service.encrypt(connection_data.config)
            
            # Create connection object
            connection = CloudConnection(
                id=connection_id,
                name=connection_data.name,
                provider=connection_data.provider,
                description=connection_data.description,
                region=connection_data.region,
                enabled=connection_data.enabled,
                status=ConnectionStatus.INACTIVE,
                config_encrypted=encrypted_config,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            # Store connection
            self.connections[connection_id] = connection
            self._save_connections()
            
            logger.info(f"Created connection: {connection.name} ({connection.provider})")
            
            return self._to_response(connection)
            
        except Exception as e:
            logger.error(f"Failed to create connection: {e}")
            raise ValueError(f"Failed to create connection: {str(e)}")
    
    def get_connection(self, connection_id: str) -> Optional[CloudConnectionResponse]:
        """
        Get a connection by ID
        
        Args:
            connection_id: Connection ID
            
        Returns:
            Connection response or None if not found
        """
        connection = self.connections.get(connection_id)
        if connection:
            return self._to_response(connection)
        return None
    
    def list_connections(
        self,
        provider: Optional[CloudProvider] = None,
        enabled_only: bool = False
    ) -> List[CloudConnectionResponse]:
        """
        List all connections with optional filtering
        
        Args:
            provider: Filter by provider
            enabled_only: Only return enabled connections
            
        Returns:
            List of connection responses
        """
        connections = list(self.connections.values())
        
        # Apply filters
        if provider:
            connections = [c for c in connections if c.provider == provider]
        
        if enabled_only:
            connections = [c for c in connections if c.enabled]
        
        # Sort by name
        connections.sort(key=lambda c: c.name)
        
        return [self._to_response(c) for c in connections]
    
    def update_connection(
        self,
        connection_id: str,
        update_data: CloudConnectionUpdate
    ) -> CloudConnectionResponse:
        """
        Update a connection
        
        Args:
            connection_id: Connection ID
            update_data: Update data
            
        Returns:
            Updated connection response
        """
        connection = self.connections.get(connection_id)
        if not connection:
            raise ValueError(f"Connection not found: {connection_id}")
        
        try:
            # Update fields
            if update_data.name is not None:
                connection.name = update_data.name
            if update_data.description is not None:
                connection.description = update_data.description
            if update_data.region is not None:
                connection.region = update_data.region
            if update_data.enabled is not None:
                connection.enabled = update_data.enabled
            
            # Update config if provided
            if update_data.config is not None:
                encrypted_config = self.encryption_service.encrypt(update_data.config)
                connection.config_encrypted = encrypted_config
            
            connection.updated_at = datetime.now(timezone.utc)
            
            self._save_connections()
            
            logger.info(f"Updated connection: {connection.name}")
            
            return self._to_response(connection)
            
        except Exception as e:
            logger.error(f"Failed to update connection: {e}")
            raise ValueError(f"Failed to update connection: {str(e)}")
    
    def delete_connection(self, connection_id: str) -> bool:
        """
        Delete a connection
        
        Args:
            connection_id: Connection ID
            
        Returns:
            True if deleted, False if not found
        """
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            del self.connections[connection_id]
            self._save_connections()
            logger.info(f"Deleted connection: {connection.name}")
            return True
        return False
    
    def get_decrypted_config(self, connection_id: str) -> Dict[str, Any]:
        """
        Get decrypted configuration for a connection
        
        Args:
            connection_id: Connection ID
            
        Returns:
            Decrypted configuration dictionary
        """
        connection = self.connections.get(connection_id)
        if not connection:
            raise ValueError(f"Connection not found: {connection_id}")
        
        try:
            return self.encryption_service.decrypt(connection.config_encrypted)
        except Exception as e:
            # Log detailed error to CLI for administrators
            logger.error(
                f"Failed to decrypt config for connection '{connection.name}' ({connection_id}). "
                f"This usually happens when ENCRYPTION_KEY is not set or has changed. "
                f"Solutions: 1) Set ENCRYPTION_KEY in .env file, "
                f"2) Run 'python fix_encryption_key.py', "
                f"3) Delete and recreate this connection. "
                f"Error details: {e}"
            )
            # User-friendly error message
            raise ValueError("Unable to decrypt connection credentials. Please check server logs or contact your administrator.")
    
    async def test_connection(self, connection_id: str) -> ConnectionTestResponse:
        """
        Test a connection
        
        Args:
            connection_id: Connection ID
            
        Returns:
            Test result
        """
        connection = self.connections.get(connection_id)
        if not connection:
            raise ValueError(f"Connection not found: {connection_id}")
        
        try:
            # Update status to testing
            connection.status = ConnectionStatus.TESTING
            connection.last_tested_at = datetime.now(timezone.utc)
            
            # Get decrypted config
            config = self.get_decrypted_config(connection_id)
            
            # Test based on provider
            if connection.provider == CloudProvider.AWS:
                result = await self._test_aws_connection(config)
            elif connection.provider == CloudProvider.IBM_CLOUD:
                result = await self._test_ibm_cloud_connection(config)
            elif connection.provider == CloudProvider.AZURE:
                result = await self._test_azure_connection(config)
            elif connection.provider == CloudProvider.GCP:
                result = await self._test_gcp_connection(config)
            elif connection.provider == CloudProvider.GENERIC:
                result = await self._test_generic_connection(config)
            else:
                result = ConnectionTestResponse(
                    success=False,
                    message=f"Unsupported provider: {connection.provider}",
                    tested_at=datetime.now(timezone.utc)
                )
            
            # Update connection status
            if result.success:
                connection.status = ConnectionStatus.ACTIVE
                connection.last_test_result = "success"
                connection.error_count = 0
                connection.last_error = None
            else:
                connection.status = ConnectionStatus.ERROR
                connection.last_test_result = "failed"
                connection.error_count += 1
                connection.last_error = result.message
            
            self._save_connections()
            
            return result
            
        except Exception as e:
            logger.error(f"Connection test failed for {connection_id}: {e}")
            connection.status = ConnectionStatus.ERROR
            connection.last_test_result = "error"
            connection.error_count += 1
            connection.last_error = str(e)
            self._save_connections()
            
            return ConnectionTestResponse(
                success=False,
                message=f"Test failed: {str(e)}",
                tested_at=datetime.now(timezone.utc)
            )
    
    async def _test_aws_connection(self, config: Dict[str, Any]) -> ConnectionTestResponse:
        """Test AWS connection"""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            # Create session with credentials
            session = boto3.Session(
                aws_access_key_id=config.get('access_key_id'),
                aws_secret_access_key=config.get('secret_access_key'),
                aws_session_token=config.get('session_token'),
                region_name=config.get('region', 'us-east-1')
            )
            
            # Test by getting caller identity
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            
            return ConnectionTestResponse(
                success=True,
                message="AWS connection successful",
                details={
                    'account': identity.get('Account'),
                    'user_id': identity.get('UserId'),
                    'arn': identity.get('Arn')
                },
                tested_at=datetime.now(timezone.utc)
            )
            
        except ClientError as e:
            return ConnectionTestResponse(
                success=False,
                message=f"AWS authentication failed: {e.response['Error']['Message']}",
                tested_at=datetime.now(timezone.utc)
            )
        except Exception as e:
            return ConnectionTestResponse(
                success=False,
                message=f"AWS connection test failed: {str(e)}",
                tested_at=datetime.now(timezone.utc)
            )
    
    async def _test_ibm_cloud_connection(self, config: Dict[str, Any]) -> ConnectionTestResponse:
        """Test IBM Cloud connection"""
        try:
            import requests
            
            # Get IAM token
            response = requests.post(
                'https://iam.cloud.ibm.com/identity/token',
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                data={
                    'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
                    'apikey': config.get('api_key')
                },
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                return ConnectionTestResponse(
                    success=True,
                    message="IBM Cloud connection successful",
                    details={
                        'token_type': token_data.get('token_type'),
                        'expires_in': token_data.get('expires_in')
                    },
                    tested_at=datetime.now(timezone.utc)
                )
            else:
                return ConnectionTestResponse(
                    success=False,
                    message=f"IBM Cloud authentication failed: {response.text}",
                    tested_at=datetime.now(timezone.utc)
                )
                
        except Exception as e:
            return ConnectionTestResponse(
                success=False,
                message=f"IBM Cloud connection test failed: {str(e)}",
                tested_at=datetime.now(timezone.utc)
            )
    
    async def _test_azure_connection(self, config: Dict[str, Any]) -> ConnectionTestResponse:
        """Test Azure connection"""
        try:
            from azure.identity import ClientSecretCredential
            from azure.mgmt.resource import ResourceManagementClient
            
            # Create credential
            credential = ClientSecretCredential(
                tenant_id=config.get('tenant_id'),
                client_id=config.get('client_id'),
                client_secret=config.get('client_secret')
            )
            
            # Test by listing resource groups
            client = ResourceManagementClient(
                credential,
                config.get('subscription_id')
            )
            
            # Just check if we can authenticate
            list(client.resource_groups.list())
            
            return ConnectionTestResponse(
                success=True,
                message="Azure connection successful",
                details={
                    'subscription_id': config.get('subscription_id'),
                    'tenant_id': config.get('tenant_id')
                },
                tested_at=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            return ConnectionTestResponse(
                success=False,
                message=f"Azure connection test failed: {str(e)}",
                tested_at=datetime.now(timezone.utc)
            )
    
    async def _test_gcp_connection(self, config: Dict[str, Any]) -> ConnectionTestResponse:
        """Test GCP connection"""
        try:
            from google.oauth2 import service_account
            from google.cloud import logging as gcp_logging
            
            # Parse credentials
            credentials = service_account.Credentials.from_service_account_info(
                json.loads(config.get('credentials_json'))
            )
            
            # Test by creating a logging client
            client = gcp_logging.Client(
                project=config.get('project_id'),
                credentials=credentials
            )
            
            # Just check if we can authenticate
            client.list_entries(max_results=1)
            
            return ConnectionTestResponse(
                success=True,
                message="GCP connection successful",
                details={
                    'project_id': config.get('project_id')
                },
                tested_at=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            return ConnectionTestResponse(
                success=False,
                message=f"GCP connection test failed: {str(e)}",
                tested_at=datetime.now(timezone.utc)
            )
    
    async def _test_generic_connection(self, config: Dict[str, Any]) -> ConnectionTestResponse:
        """Test generic connection"""
        try:
            import requests
            
            # Build headers
            headers = config.get('custom_headers', {}).copy()
            
            auth_type = config.get('auth_type', 'api_key')
            if auth_type == 'api_key':
                headers['X-API-Key'] = config.get('api_key')
            elif auth_type == 'bearer':
                headers['Authorization'] = f"Bearer {config.get('bearer_token')}"
            
            # Test connection
            response = requests.get(
                config.get('endpoint_url'),
                headers=headers,
                timeout=10
            )
            
            if response.status_code < 400:
                return ConnectionTestResponse(
                    success=True,
                    message="Generic connection successful",
                    details={
                        'status_code': response.status_code,
                        'endpoint': config.get('endpoint_url')
                    },
                    tested_at=datetime.now(timezone.utc)
                )
            else:
                return ConnectionTestResponse(
                    success=False,
                    message=f"Connection returned status {response.status_code}",
                    tested_at=datetime.now(timezone.utc)
                )
                
        except Exception as e:
            return ConnectionTestResponse(
                success=False,
                message=f"Generic connection test failed: {str(e)}",
                tested_at=datetime.now(timezone.utc)
            )
    
    def _to_response(self, connection: CloudConnection) -> CloudConnectionResponse:
        """Convert connection to response model"""
        # Get config summary
        try:
            config = self.get_decrypted_config(connection.id)
            config_summary = self.encryption_service.get_config_summary(
                config,
                connection.provider.value
            )
        except Exception:
            config_summary = {}
        
        return CloudConnectionResponse(
            id=connection.id,
            name=connection.name,
            provider=connection.provider,
            description=connection.description,
            region=connection.region,
            enabled=connection.enabled,
            status=connection.status,
            created_at=connection.created_at,
            updated_at=connection.updated_at,
            last_tested_at=connection.last_tested_at,
            last_test_result=connection.last_test_result,
            events_processed=connection.events_processed,
            last_event_at=connection.last_event_at,
            error_count=connection.error_count,
            last_error=connection.last_error,
            config_summary=config_summary
        )
    
    def update_connection_stats(
        self,
        connection_id: str,
        events_processed: Optional[int] = None,
        last_event_at: Optional[datetime] = None,
        error: Optional[str] = None
    ):
        """
        Update connection statistics
        
        Args:
            connection_id: Connection ID
            events_processed: Number of events processed (incremental)
            last_event_at: Last event timestamp
            error: Error message if any
        """
        connection = self.connections.get(connection_id)
        if not connection:
            return
        
        if events_processed is not None:
            connection.events_processed += events_processed
        
        if last_event_at is not None:
            connection.last_event_at = last_event_at
        
        if error is not None:
            connection.error_count += 1
            connection.last_error = error
            connection.status = ConnectionStatus.ERROR
        
        self._save_connections()


# Global connection manager instance
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager


# Made with Bob