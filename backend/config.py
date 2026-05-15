"""
Configuration management for AuditAura
Handles environment variables and application settings
"""
import os
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
import logging
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)


class Config(BaseModel):
    """Application configuration"""
    
    # Encryption Configuration
    encryption_key: Optional[str] = Field(default=None)
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(default=None)
    openai_enabled: bool = Field(default=False)
    
    # Ollama Configuration
    ollama_host: str = Field(default='http://ollama:11434')
    ollama_model: str = Field(default='phi4-mini')
    ollama_enabled: bool = Field(default=False)
    
    # LM Studio Configuration
    lm_studio_host: str = Field(default='http://localhost:1234')
    lm_studio_model: str = Field(default='google/gemma-2-9b')
    lm_studio_enabled: bool = Field(default=False)
    
    # Google Gemini Configuration
    google_api_key: Optional[str] = Field(default=None)
    gemini_model: str = Field(default='gemini-1.5-flash')
    gemini_enabled: bool = Field(default=False)
    
    # OpenCode.ai Zen Configuration
    opencode_api_key: Optional[str] = Field(default=None)
    opencode_model: str = Field(default='minimax-2.5-free')
    opencode_base_url: str = Field(default='https://api.opencode.ai/v1')
    opencode_enabled: bool = Field(default=True)
    
    # Anthropic/OpenCode Zen Anthropic-Compatible Configuration
    anthropic_api_key: Optional[str] = Field(default=None)
    anthropic_model: str = Field(default='minimax-m2.5-free')
    anthropic_base_url: str = Field(default='https://opencode.ai/zen')
    enable_tool_search: bool = Field(default=False)
    
    # Email Configuration
    smtp_host: Optional[str] = Field(default=None)
    smtp_port: int = Field(default=587)
    smtp_user: Optional[str] = Field(default=None)
    smtp_password: Optional[str] = Field(default=None)
    smtp_from: str = Field(default='noreply@auditaura.com')
    
    # Slack Configuration
    slack_webhook_url: Optional[str] = Field(default=None)
    
    # GitHub Configuration
    github_token: Optional[str] = Field(default=None)
    github_repo_owner: Optional[str] = Field(default=None)
    github_repo_name: Optional[str] = Field(default=None)
    
    # IBM Cloud Configuration
    ibm_cloud_api_key: Optional[str] = Field(default=None)
    ibm_cloud_region: str = Field(default='us-south')
    ibm_activity_tracker_instance_id: Optional[str] = Field(default=None)
    ibm_monitoring_instance_id: Optional[str] = Field(default=None)
    ibm_logs_instance_id: Optional[str] = Field(default=None)
    ibm_cloud_enabled: bool = Field(default=False)
    
    # Application Configuration
    log_level: str = Field(default='INFO')
    mock_mode: bool = Field(default=True)  # Only affects dashboard fallback data, not event sources
    compliance_check_interval: int = Field(default=30)
    
    # Database Configuration
    database_url: Optional[str] = Field(default=None)
    
    # Vector Store Configuration
    vector_store_path: str = Field(default='./data/vector_store')
    
    # API Configuration
    api_host: str = Field(default='0.0.0.0')
    api_port: int = Field(default=8000)
    
    @field_validator('encryption_key')
    @classmethod
    def validate_encryption_key(cls, v):
        # Warn if encryption key is not set or is a placeholder
        if not v or v == 'your_encryption_key_here':
            logger.warning(
                'ENCRYPTION_KEY is not set or is a placeholder. '
                'A temporary key will be generated, but encrypted data will not persist across restarts. '
                'Generate a key with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
            )
        return v
    
    @field_validator('openai_api_key')
    @classmethod
    def validate_openai_key(cls, v, info):
        # Only validate if OpenAI is enabled
        if info.data.get('openai_enabled', False):
            if not v or v == 'your_openai_api_key_here':
                raise ValueError('OPENAI_API_KEY must be set to a valid API key when OPENAI_ENABLED=true')
        return v
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'LOG_LEVEL must be one of {valid_levels}')
        return v.upper()
    
    @field_validator('compliance_check_interval')
    @classmethod
    def validate_interval(cls, v):
        if v < 1:
            raise ValueError('COMPLIANCE_CHECK_INTERVAL must be at least 1 second')
        return v
    
    model_config = ConfigDict(
        protected_namespaces=(),
        case_sensitive=False
    )


def load_config() -> Config:
    """Load and validate configuration from environment"""
    try:
        config = Config(
            encryption_key=os.getenv('ENCRYPTION_KEY'),
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            openai_enabled=os.getenv('OPENAI_ENABLED', 'false').lower() == 'true',
            ollama_host=os.getenv('OLLAMA_HOST', 'http://ollama:11434'),
            ollama_model=os.getenv('OLLAMA_MODEL', 'phi4-mini'),
            ollama_enabled=os.getenv('OLLAMA_ENABLED', 'false').lower() == 'true',
            lm_studio_host=os.getenv('LM_STUDIO_HOST', 'http://localhost:1234'),
            lm_studio_model=os.getenv('LM_STUDIO_MODEL', 'google/gemma-2-9b'),
            lm_studio_enabled=os.getenv('LM_STUDIO_ENABLED', 'true').lower() == 'true',
            google_api_key=os.getenv('GOOGLE_API_KEY'),
            gemini_model=os.getenv('GEMINI_MODEL', 'gemini-1.5-flash'),
            gemini_enabled=os.getenv('GEMINI_ENABLED', 'false').lower() == 'true',
            opencode_api_key=os.getenv('OPENCODE_API_KEY'),
            opencode_model=os.getenv('OPENCODE_MODEL', 'minimax-2.5-free'),
            opencode_base_url=os.getenv('OPENCODE_BASE_URL', 'https://api.opencode.ai/v1'),
            opencode_enabled=os.getenv('OPENCODE_ENABLED', 'true').lower() == 'true',
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            anthropic_model=os.getenv('ANTHROPIC_MODEL', 'minimax-m2.5-free'),
            anthropic_base_url=os.getenv('ANTHROPIC_BASE_URL', 'https://opencode.ai/zen'),
            enable_tool_search=os.getenv('ENABLE_TOOL_SEARCH', 'false').lower() == 'true',
            smtp_host=os.getenv('SMTP_HOST'),
            smtp_port=int(os.getenv('SMTP_PORT', '587')),
            smtp_user=os.getenv('SMTP_USER'),
            smtp_password=os.getenv('SMTP_PASSWORD'),
            smtp_from=os.getenv('SMTP_FROM', 'noreply@auditaura.com'),
            slack_webhook_url=os.getenv('SLACK_WEBHOOK_URL'),
            github_token=os.getenv('GITHUB_TOKEN'),
            github_repo_owner=os.getenv('GITHUB_REPO_OWNER'),
            github_repo_name=os.getenv('GITHUB_REPO_NAME'),
            ibm_cloud_api_key=os.getenv('IBM_CLOUD_API_KEY'),
            ibm_cloud_region=os.getenv('IBM_CLOUD_REGION', 'us-south'),
            ibm_activity_tracker_instance_id=os.getenv('IBM_ACTIVITY_TRACKER_INSTANCE_ID'),
            ibm_monitoring_instance_id=os.getenv('IBM_MONITORING_INSTANCE_ID'),
            ibm_logs_instance_id=os.getenv('IBM_LOGS_INSTANCE_ID'),
            ibm_cloud_enabled=os.getenv('IBM_CLOUD_ENABLED', 'false').lower() == 'true',
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            mock_mode=os.getenv('MOCK_MODE', 'true').lower() == 'true',
            compliance_check_interval=int(os.getenv('COMPLIANCE_CHECK_INTERVAL', '30')),
            database_url=os.getenv('DATABASE_URL'),
            vector_store_path=os.getenv('VECTOR_STORE_PATH', './data/vector_store'),
            api_host=os.getenv('API_HOST', '0.0.0.0'),
            api_port=int(os.getenv('API_PORT', '8000'))
        )
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        logger.info(f"Configuration loaded successfully (Mock Mode for Dashboard: {config.mock_mode})")
        return config
        
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise


# Global config instance
config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance"""
    global config
    if config is None:
        config = load_config()
    return config

# Made with Bob
