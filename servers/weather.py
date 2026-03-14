from typing import Any
import httpx
import logging
from fastmcp import FastMCP
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import config

# Configure logging
logging.basicConfig(level=getattr(logging, config.weather.log_level))

mcp = FastMCP("weather")

NWS_API_BASE = config.weather.nws_api_base
USER_AGENT = config.weather.user_agent


async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=config.weather.timeout)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error {e.response.status_code}: {e}")
            return None
        except httpx.TimeoutException:
            logging.error(f"Request timeout for {url}")
            return None
        except Exception as e:
            logging.error(f"NWS request failed: {e}")
            return None


def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]

    return f"""
Event: {props.get("event", "Unknown")}
Area: {props.get("areaDesc", "Unknown")}
Severity: {props.get("severity", "Unknown")}
Description: {props.get("description", "No description available")}
Instructions: {props.get("instruction", "No specific instructions provided")}
"""


@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    logging.info(f"MCP TOOL CALLED -> get_alerts({state})")
    
    # Validate input
    state = state.upper().strip()
    if len(state) != 2 or not state.isalpha():
        return "Error: State must be a 2-letter US state code (e.g., CA, NY)"

    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]

    return "\n---\n".join(alerts)


@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    logging.info(f"MCP TOOL CALLED -> get_forecast({latitude}, {longitude})")
    
    # Validate coordinates
    if not (-90 <= latitude <= 90):
        return "Error: Latitude must be between -90 and 90"
    if not (-180 <= longitude <= 180):
        return "Error: Longitude must be between -180 and 180"

    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    periods = forecast_data["properties"]["periods"]
    forecasts = []

    for period in periods[:5]:
        forecast = f"""
{period["name"]}:
Temperature: {period["temperature"]}°{period["temperatureUnit"]}
Wind: {period["windSpeed"]} {period["windDirection"]}
Forecast: {period["detailedForecast"]}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)


def main():
    """Start MCP server."""
    logging.info("Starting Weather MCP Server...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()