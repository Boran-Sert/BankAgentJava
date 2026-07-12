"""Provides core functionalities for the config module."""
import yaml
from pydantic import BaseModel
from typing import Literal
from pathlib import Path

class LLMSettings(BaseModel):
    """Defines the Llmsettings structure."""
    mode: Literal["ollama", "gpt-oss"]
    ollama_model: str
    gpt_oss_base_url: str
    gpt_oss_api_key: str
    temperature: float

class VectorDBSettings(BaseModel):
    """Defines the Vectordbsettings structure."""
    persist_dir: str
    routing_threshold: float
    mapping_threshold: float
    top_k_tools: int

class LoggerSettings(BaseModel):
    """Defines the Loggersettings structure."""
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]
    format: Literal["json", "console"]

class RedisSettings(BaseModel):
    """Defines the Redissettings structure."""
    url: str

class Settings(BaseModel):
    """Defines the Settings structure."""
    llm: LLMSettings
    vector_db: VectorDBSettings
    logger: LoggerSettings
    redis: RedisSettings

def load_settings(config_path: str = "config.yaml") -> Settings:
    """Executes the Load settings operation."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")
    
    with open(path, "r", encoding="utf-8") as f:
        config_dict = yaml.safe_load(f)
        
    return Settings(**config_dict)

# Global settings instance
settings = load_settings()
