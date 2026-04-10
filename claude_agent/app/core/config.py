from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # API Configuration
    api_title: str = "Claude Agent"
    api_version: str = "0.1.0"

    # Claude API Configuration
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"

    # Database Configuration
    database_url: str = "sqlite:///claude_agent.db"

    # Session Configuration
    session_expiry_hours: int = 24

    # News Aggregation Configuration
    default_fetch_interval_minutes: int = 60
    max_feed_items_per_source: int = 100
    feed_request_timeout_seconds: int = 30
    feed_user_agent: str = "ClaudeAgentNewsAggregator/1.0"

    # AI Processing Configuration
    enable_ai_processing: bool = True
    max_articles_per_batch: int = 10
    ai_processing_timeout_seconds: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True

# Load settings
settings = Settings()

# Warn if ANTHROPIC_API_KEY is not set
if not settings.anthropic_api_key:
    import warnings
    warnings.warn(
        "ANTHROPIC_API_KEY environment variable is not set. "
        "Please set it in .env file or environment variables. "
        "The application will start but Claude API calls will fail."
    )
