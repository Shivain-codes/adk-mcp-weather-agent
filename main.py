"""
FastAPI HTTP server for the ADK MCP Weather Intelligence Agent.
Endpoints: /weather, /chat, /health, /docs
"""

import os
import uuid
import logging
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from agent import root_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Schemas ────────────────────────────────────────────────────────────────────

class WeatherRequest(BaseModel):
    city: str = Field(..., description="City name: london, new_york, tokyo, mumbai, sydney")

class ChatRequest(BaseModel):
    message: str = Field(..., description="Free-form message to the weather agent")

class AgentResponse(BaseModel):
    response: str
    session_id: str
    agent_name: str

# ── Core runner ────────────────────────────────────────────────────────────────

async def run_agent(message: str) -> str:
    """
    Creates a fresh session per request and awaits all async ADK calls.
    """
    session_id = uuid.uuid4().hex
    app_name   = "mcp-weather-agent"
    user_id    = "api-user"

    svc = InMemorySessionService()

    # create_session is async in ADK — must be awaited
    await svc.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )

    runner = Runner(
        agent=root_agent,
        app_name=app_name,
        session_service=svc,
    )

    content = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=message)],
    )

    final_response = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response = "".join(
                    p.text for p in event.content.parts
                    if hasattr(p, "text") and p.text
                )

    return final_response.strip() or "No response generated."

# ── FastAPI App ────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not os.environ.get("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY is not set. Configure it before starting the service.")
    logger.info("MCP Weather Agent starting...")
    yield
    logger.info("MCP Weather Agent shutting down.")

app = FastAPI(
    title="ADK MCP Weather Intelligence Agent",
    description=(
        "An AI weather agent using Google ADK + MCP + Gemini 2.0 Flash. "
        "Retrieves structured weather data via MCP filesystem tool and generates intelligent reports."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "agent": root_agent.name,
        "status": "running",
        "model": "gemini-2.0-flash",
        "mcp_tool": "@modelcontextprotocol/server-filesystem",
        "data_source": "weather_data/ directory (5 cities)",
        "available_cities": ["london", "new_york", "tokyo", "mumbai", "sydney"],
        "endpoints": {
            "weather": "POST /weather  — Get weather report for a city",
            "chat":    "POST /chat    — Free-form weather questions",
            "health":  "GET  /health  — Health check",
            "docs":    "GET  /docs    — Swagger UI",
        },
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "agent": root_agent.name,
        "mcp": "connected",
    }

@app.post("/weather", response_model=AgentResponse)
async def get_weather(req: WeatherRequest):
    """
    Get an AI-generated weather report for a city.
    MCP retrieves the structured JSON data; Gemini generates the report.

    Available cities: london, new_york, tokyo, mumbai, sydney
    """
    message = (
        f"Get the current weather report for {req.city}. "
        f"Use the MCP filesystem tool to read the weather data file for this city, "
        f"then generate a helpful weather report based on the retrieved data."
    )
    try:
        response = await run_agent(message)
        return AgentResponse(
            response=response,
            session_id=uuid.uuid4().hex,
            agent_name=root_agent.name,
        )
    except Exception as e:
        logger.error(f"Weather error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=AgentResponse)
async def chat(req: ChatRequest):
    """
    Ask the weather agent any question.
    It will use MCP to retrieve data and respond intelligently.
    """
    try:
        response = await run_agent(req.message)
        return AgentResponse(
            response=response,
            session_id=uuid.uuid4().hex,
            agent_name=root_agent.name,
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ── Entry ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
