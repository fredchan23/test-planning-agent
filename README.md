# Test-Planning Agent (ADK 2.0)

A powerful, automated Quality Assurance (QA) Architect and Test Planner designed using the **Google Agent Development Kit (ADK) 2.0**. This agent crawls a web-based System Under Test (SUT), maps user intents and business requirements (PRD) to the crawled DOM structure, generates a deep scenario matrix (including positive, negative, boundary, and implicit cases), and grounds the resulting test plan into Playwright-compatible semantic element selectors.

---

## 🚀 Key Features

*   **Semantic DOM Crawler**: Lightweight, asynchronous crawler (using `aiohttp` and `BeautifulSoup`) that scrapes and analyzes interactive page elements (roles, labels, IDs, CSS selectors, options).
*   **Intent Mapping**: Correlates features/requirements defined in a Product Requirement Document (PRD) to discovered page elements.
*   **Deep Scenario Matrix**: Generates a test case matrix with prioritized positive, negative, and edge-case scenarios (Priority 0, 1, and 2).
*   **Playwright Selector Grounding**: Compiles test steps with stable semantic accessibility tree targets (e.g., matching ARIA roles and labels).
*   **Multi-Agent Workflow**: Leverages a structured ADK workflow containing:
    *   `parse_input` (Node)
    *   `run_crawler` (Node)
    *   `intent_mapper` (LlmAgent)
    *   `scenario_matrix_agent` (LlmAgent)
    *   `element_grounding_agent` (LlmAgent)
    *   `compile_output` (Node)

---

## 🛠️ Tech Stack

*   **Core**: Python `3.11` to `3.13`
*   **Agent framework**: Google ADK 2.0
*   **HTML Parsing**: BeautifulSoup4 & aiohttp
*   **Build/Env Manager**: `uv` (recommended) or standard `hatchling` / `pip`

---

## 📦 Setup Instructions

### Prerequisites
*   Python **3.11**, **3.12**, or **3.13**
*   Google Cloud Platform (GCP) credentials or a Google Gemini API Key

### 1. Clone & Set Up the Virtual Environment
We recommend using the modern [uv](https://github.com/astral-sh/uv) package manager for fast, reliable setups.

```bash
# Clone the repository (if not already cloned)
git clone <your-repo-url>
cd test-planning-agent

# Create a virtual environment and install dependencies using uv
uv sync
```

Alternatively, you can use standard Python toolchains:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory. This file is excluded from git tracking.

```bash
# Set up environment variables
cp .env.example .env  # Or create it manually
```

Configure the following variables:

#### A. If using Vertex AI / Google Cloud Enterprise (Default)
```env
GOOGLE_GENAI_USE_ENTERPRISE="True"
GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
GOOGLE_CLOUD_LOCATION="global"
```
Ensure you have authenticated with GCP locally:
```bash
gcloud auth application-default login
```

#### B. If using Google GenAI Developer API (Gemini API Key)
```env
GOOGLE_GENAI_USE_ENTERPRISE="False"
GEMINI_API_KEY="your-gemini-api-key"
```

---

## 🏃 Running the Agent

You can execute the test planning workflow from your terminal.

```bash
# Run the agent against the default SUT (Singapore Healthspan Simulator)
uv run python -m test_planner_agent.main

# Run the agent against a custom URL with a custom PRD file
uv run python -m test_planner_agent.main --url "https://example.com" --prd "docs/prd.md"
```

### Arguments:
*   `--url`: The Target SUT URL to explore and audit (default: `https://healthspan.assurecraft.org`).
*   `--prd`: Path to the PRD file in markdown (optional).

Once completed, the agent will generate and compile a complete test plan document named **`test_plan.md`** in your current working directory.

---

## 🧪 Testing and Evaluation

### Run Unit Tests
To verify that the crawler and agent workflow structural mapping works correctly:
```bash
uv run pytest
```

### Run ADK Evaluations
The project includes a test evaluation suite configuration (`tests/eval/`) with test datasets to evaluate the quality of the generated test plans.

To run agent evaluations using the ADK `acli` CLI tool:
```bash
# Install evaluation dependencies
uv sync --extra eval

# Run agent evaluations
acli eval run
```

---

## 📂 Project Structure

```
├── test_planner_agent/
│   ├── __init__.py
│   ├── agent.py         # Main agent node definitions and ADK workflow graph
│   ├── app.py           # Fast API / Web deployment wrapper (if run as service)
│   ├── config.py        # Default variables, path configurations and model configs
│   ├── crawler.py       # Static DOM audit crawler utilizing beautifulsoup/aiohttp
│   ├── main.py          # Command-Line Interface (CLI) entry point
│   └── prd_sample.md    # Reference PRD for Singapore Healthspan Simulator
├── tests/
│   ├── eval/
│   │   ├── datasets/
│   │   │   └── basic-dataset.json  # ADK evaluation dataset cases
│   │   └── eval_config.yaml         # ADK evaluation metrics configuration
│   ├── test_agent.py    # Unit tests for workflow structure
│   └── test_crawler.py  # Unit tests for DOM parsing and selector extraction
├── Dockerfile           # Docker configuration for hosting or deploying
├── pyproject.toml       # Hatchling project build specifications and dependencies
├── uv.lock              # Lock file for package dependencies
└── agents-cli-manifest.yaml  # Deployment/Evaluation metadata for ADK CLI
```
