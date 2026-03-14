import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class WeatherConfig:
    nws_api_base: str = "https://api.weather.gov"
    user_agent: str = "weather-mcp-server/1.0"
    timeout: float = 30.0
    max_retries: int = 3
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

@dataclass
class JiraConfig:
    url: Optional[str] = os.getenv("JIRA_URL")
    email: Optional[str] = os.getenv("JIRA_EMAIL")
    api_token: Optional[str] = os.getenv("JIRA_API_TOKEN")
    timeout: float = 30.0
    max_retries: int = 3
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

class Config:
    weather = WeatherConfig()
    jira = JiraConfig()

config = Config()

