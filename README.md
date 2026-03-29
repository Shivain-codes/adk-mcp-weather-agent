# 🌤️ ADK MCP Weather Intelligence Agent

> An AI agent built with **Google ADK** + **MCP** + **Gemini 2.5 Flash**, deployed on **Cloud Run**.
> Retrieves structured weather data via MCP and generates intelligent weather reports.

[![Google ADK](https://img.shields.io/badge/Google%20ADK-1.2.1-4285F4?logo=google)](https://google.github.io/adk-docs/)
[![MCP](https://img.shields.io/badge/MCP-Filesystem-34A853)](https://modelcontextprotocol.io/)
[![Gemini](https://img.shields.io/badge/Gemini-2.0%20Flash-34A853)](https://ai.google.dev/)
[![Cloud Run](https://img.shields.io/badge/Cloud%20Run-Ready-4285F4)](https://cloud.google.com/run)

---

## 📋 Project Overview

| Property | Value |
|----------|-------|
| **Framework** | Google ADK v1.2.1 |
| **MCP Tool** | `@modelcontextprotocol/server-filesystem` |
| **Model** | Gemini 2.5 Flash |
| **Data Source** | Structured JSON weather files (5 cities) |
| **Deployment** | Google Cloud Run |

---

## 🧠 Architecture

```
HTTP Request
     │
     ▼
┌─────────────────────────────────┐
│         FastAPI Server          │
│    POST /weather  POST /chat    │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│         ADK Runner              │
│   (session + event management)  │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│    weather_intelligence_agent   │
│    model: gemini-2.5-flash      │
│    tools: [MCPToolset]          │
└──────────────┬──────────────────┘
               │  MCP Protocol
               ▼
┌─────────────────────────────────┐
│  @modelcontextprotocol/         │
│  server-filesystem (via npx)    │
│  Reads weather_data/*.json      │
└─────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│     Gemini 2.5 Flash            │
│  Generates weather report from  │
│  retrieved MCP data             │
└─────────────────────────────────┘
```

---

## 🌍 Available Cities

| City | File |
|------|------|
| London | `weather_data/london.json` |
| New York | `weather_data/new_york.json` |
| Tokyo | `weather_data/tokyo.json` |
| Mumbai | `weather_data/mumbai.json` |
| Sydney | `weather_data/sydney.json` |

---

## 🚀 Quick Start

```bash
# 1. Clone repo
git clone https://github.com/YOUR_USERNAME/adk-mcp-weather-agent
cd adk-mcp-weather-agent

# 2. Set API key
export GEMINI_API_KEY=your_key_here

# 3. Run locally
pip install -r requirements.txt
python main.py
```

The service starts on `http://localhost:8080`.

---

## 🌐 API Reference

### `GET /health`
```bash
curl https://YOUR_URL/health
```

### `POST /weather`
```bash
curl -X POST https://YOUR_URL/weather \
  -H "Content-Type: application/json" \
  -d '{"city": "tokyo"}'
```

### `POST /chat`
```bash
curl -X POST https://YOUR_URL/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What should I wear in London today?"}'
```

### `GET /docs`
Interactive Swagger UI — test all endpoints in browser.

---

## ☁️ Deploy to Cloud Run

```bash
export PROJECT_ID=your-gcp-project-id
export GEMINI_API_KEY=your_gemini_key

# Build
gcloud builds submit \
  --tag gcr.io/$PROJECT_ID/adk-mcp-weather-agent:latest .

# Deploy
gcloud run deploy adk-mcp-weather-agent \
  --image gcr.io/$PROJECT_ID/adk-mcp-weather-agent:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --set-env-vars "GEMINI_API_KEY=$GEMINI_API_KEY,GOOGLE_GENAI_USE_VERTEXAI=FALSE"
```

## 🔁 Deploy to Cloud Run via GitHub Actions

This repository includes a workflow at `.github/workflows/deploy-cloud-run.yml`.

1. Create GitHub Repository Variables:
  - `GCP_PROJECT_ID`
  - `GCP_REGION` (example: `us-central1`)
  - `CLOUD_RUN_SERVICE` (example: `adk-mcp-weather-agent`)

2. Create GitHub Repository Secrets:
  - `GCP_WORKLOAD_IDENTITY_PROVIDER`
  - `GCP_SERVICE_ACCOUNT_EMAIL`
  - `GEMINI_API_KEY`

3. Grant required IAM roles to the deploy service account:
  - `roles/run.admin`
  - `roles/iam.serviceAccountUser`
  - `roles/cloudbuild.builds.editor`
  - `roles/artifactregistry.writer`

4. Push to `main` (or run the workflow manually from Actions tab).

The workflow will build from source using your Dockerfile and deploy directly to Cloud Run.

---

## 📁 Project Structure

```
adk-mcp-weather-agent/
├── .github/workflows/deploy-cloud-run.yml  # GitHub Actions deployment
├── agent.py                                # ADK Agent + MCPToolset definition
├── main.py                                 # FastAPI server + ADK Runner
├── requirements.txt                        # Python dependencies
├── Dockerfile                              # Multi-stage build (Python + Node.js for MCP)
├── .env.example                            # Required environment variables template
├── weather_data/                           # Structured JSON data files (MCP data source)
│   ├── london.json
│   ├── new_york.json
│   ├── tokyo.json
│   ├── mumbai.json
│   └── sydney.json
└── README.md
```

---

## 🔧 How MCP Works in This Project

1. Agent is configured with `MCPToolset(StdioServerParameters(command="npx", args=["@modelcontextprotocol/server-filesystem", "weather_data/"]))`
2. When a weather request comes in, Gemini decides to call the MCP filesystem tool
3. MCP server reads the appropriate `city.json` file and returns structured data
4. Gemini receives the JSON data and generates a natural language weather report
5. FastAPI returns the final response to the caller
