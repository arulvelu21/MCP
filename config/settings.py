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

@dataclass
class ConfluenceConfig:
    url: Optional[str] = os.getenv("CONFLUENCE_URL")           # Same as JIRA_URL usually
    email: Optional[str] = os.getenv("CONFLUENCE_EMAIL")       # Same as JIRA_EMAIL usually
    api_token: Optional[str] = os.getenv("CONFLUENCE_API_TOKEN") # Same token as Jira
    timeout: float = 30.0
    max_retries: int = 3
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


@dataclass
class ZendeskConfig:
    url: Optional[str] = os.getenv("ZENDESK_URL")           # e.g. https://yourcompany.zendesk.com
    email: Optional[str] = os.getenv("ZENDESK_EMAIL")
    api_token: Optional[str] = os.getenv("ZENDESK_API_TOKEN")
    timeout: float = 30.0
    max_retries: int = 3
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

class Config:
    weather = WeatherConfig()
    jira = JiraConfig()
    confluence = ConfluenceConfig()
    zendesk = ZendeskConfig()

config = Config()
