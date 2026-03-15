import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load .env BEFORE dataclass defaults are evaluated
load_dotenv()

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

@dataclass
class AzureOpenAIConfig:
    api_key: Optional[str]         = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint: Optional[str]        = os.getenv("AZURE_OPENAI_ENDPOINT")        # e.g. https://<your-resource>.openai.azure.com/
    deployment_name: Optional[str] = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") # e.g. gpt-4o
    api_version: str               = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")

class Config:
    weather = WeatherConfig()
    jira = JiraConfig()
    confluence = ConfluenceConfig()
    zendesk = ZendeskConfig()
    azure_openai = AzureOpenAIConfig()

config = Config()
