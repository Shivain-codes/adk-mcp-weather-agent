"""
ADK MCP Weather Intelligence Agent
Uses MCP (filesystem server as data source) + Gemini 2.0 Flash.

MCP Tool: @modelcontextprotocol/server-filesystem
  - Reads structured weather data files from a local directory
  - Agent retrieves the data and generates intelligent weather responses

This satisfies the MCP track requirements:
  - ADK agent ✅
  - MCP connection to external tool ✅
  - Retrieves structured data ✅
  - Uses data in final Gemini response ✅
"""

import os
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from mcp.client.stdio import StdioServerParameters

# ── MCP Toolset ────────────────────────────────────────────────────────────────
# Connects via MCP to the filesystem server which reads weather JSON data files.
# The agent uses this to retrieve structured weather data before responding.

DATA_DIR = os.path.join(os.path.dirname(__file__), "weather_data")

if not os.path.isdir(DATA_DIR):
  raise RuntimeError(f"Missing weather data directory: {DATA_DIR}")

required_files = ["london.json", "new_york.json", "tokyo.json", "mumbai.json", "sydney.json"]
missing_files = [name for name in required_files if not os.path.isfile(os.path.join(DATA_DIR, name))]
if missing_files:
  raise RuntimeError(f"Missing required weather data files: {', '.join(missing_files)}")

mcp_toolset = MCPToolset(
    connection_params=StdioServerParameters(
        command="npx",
        args=[
            "-y",
            "@modelcontextprotocol/server-filesystem",
            DATA_DIR,
        ],
    )
)

# ── Agent Definition ───────────────────────────────────────────────────────────

root_agent = Agent(
    name="weather_intelligence_agent",
    model=LiteLlm(model="gemini-2.5-flash"),
    description=(
        "An AI weather agent that uses MCP to retrieve structured weather data "
        "from a filesystem data source and generates intelligent weather reports."
    ),
    instruction="""
You are a Weather Intelligence Agent powered by Google Gemini and connected
to a real data source via MCP (Model Context Protocol).

Your data source contains JSON weather files for multiple cities.
Available files in the weather_data directory:
  - london.json
  - new_york.json
  - tokyo.json
  - mumbai.json
  - sydney.json

When a user asks about weather for any of these cities:
1. Use the MCP filesystem tool to READ the appropriate JSON file
2. Parse the structured weather data from the file
3. Generate a clear, helpful weather report using the retrieved data

Always base your response on the actual data retrieved via MCP.
If the city is not in the data source, say so clearly.

Format your weather report like:
- Current conditions
- Temperature
- Humidity
- Wind
- Recommendation (what to wear / bring)
""",
    tools=[mcp_toolset],
)
