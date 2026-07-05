# TestMind: Agentic Test Planning with Google ADK 2.0

An autonomous Quality Assurance (QA) agent that crawls your web application, reads your Product Requirements Document (PRD), and outputs a production-ready, grounded test plan in under 60 seconds.

[![TestMind Demo Video](https://img.youtube.com/vi/TovgDX-LRZQ/0.jpg)](https://youtu.be/TovgDX-LRZQ)

[Watch the YouTube Demo Video](https://youtu.id/TovgDX-LRZQ)

---

## Overview and The Problem

When a QA engineer joins an organization mid-project, two blockers hit at once:
1. The application already exists, but internal documentation (PRDs, specs) is missing or stale.
2. There is no test plan, yet they are expected to write scripts and find bugs immediately.

TestMind bridges this documentation gap. By accepting a live application URL (System Under Test - SUT) and an optional PRD, it:
- Audits the app's interactive elements and structure.
- Maps UI elements to business goals, journeys, and checkpoints.
- Generates a comprehensive scenario matrix (happy, sad, and boundary cases).
- Grounds test cases in accessibility markers (ARIA roles, CSS selectors) to form a Semantic Target Mapping (STM) ready for automated test suites (e.g., Playwright or Cypress).

---

## Technical Architecture

TestMind is powered by a multi-agent sequential workflow built with Google ADK 2.0 (`google-adk[gcp]`).

```
  [START]
     │
     ▼
  [1. parse_input (Deterministic)]
     │
     ▼
  [2. run_crawler (BeautifulSoup4 + aiohttp)]
     │
     ▼
  [3. intent_mapper (LlmAgent)]
     │
     ▼
  [4. scenario_matrix_agent (LlmAgent)]
     │
     ▼
  [5. element_grounding_agent (LlmAgent)]
     │
     ▼
  [6. compile_output (Deterministic)]
     │
     ▼
  [Test Plan Generated]
```

### ADK 2.0 Sequential Workflow Nodes

| Node | Type | Responsibility |
| :--- | :--- | :--- |
| `parse_input` | Deterministic | Normalizes the target SUT URL and loads/reads the PRD into session state. |
| `run_crawler` | Deterministic | Crawls the SUT, extracting interactive elements (buttons, inputs, dropdowns, ARIA roles, options) into a simplified DOM representation. |
| `intent_mapper` | `LlmAgent` | Maps crawled elements to top-level business Goals, Journeys (E2E user paths), and Checkpoints. |
| `scenario_matrix_agent` | `LlmAgent` | Performs boundary analysis and risk-based categorization (Priority 0, 1, 2) across happy-path, sad-path, and edge scenarios. |
| `element_grounding_agent` | `LlmAgent` | Establishes test pre-conditions, synthetic data parameters (e.g., `age=45`), and logical outcomes. Compiles the Semantic Target Mapping (STM). |
| `compile_output` | Deterministic | Assembles all agent responses into the final Markdown test plan and embeds the STM as a structured JSON hand-off. |

---

## Key Features

- **Lightweight Crawler:** Next.js and React SSR-optimized parsing using `BeautifulSoup4` and `aiohttp`. No heavy headless-Chrome binary dependencies required, keeping Cloud Run instances lean.
- **Robust SSE Streaming:** Served via a FastAPI backend implementing Server-Sent Events (SSE) at `/api/generate`. A background `asyncio.Queue` buffers LLM state events to survive GCP Cloud Run proxy idle timeouts.
- **Glassmorphic Dashboard:** Sleek, modern front-end UI utilizing Outfit and Space Grotesk typography, featuring interactive log streaming, rendered Markdown previews, and a raw copy-to-clipboard console.
- **Semantic Grounding:** Emits a structured locator mapping connecting logic steps to stable accessibility and CSS selectors.

---

## Getting Started

### Prerequisites

- **Python:** `3.11` to `3.13`
- **Google Cloud Platform (GCP) Project:** Active billing and access to Vertex AI services.

### Installation

Clone the repository and install the package using `uv` (recommended) or `pip`:

```bash
# Optional: Setup a virtual environment
python -m venv .venv
source .venv/bin/activate # On Windows: .venv\Scripts\activate

# Install dependencies and the package
pip install -e .
```

To run with LLM evaluation packages:
```bash
pip install -e .[eval]
```

### Environment Configuration

1. Authenticate with your Google Cloud Account:
   ```bash
   gcloud auth application-default login
   ```

2. Create a `.env` file in the root directory:
   ```env
   GOOGLE_GENAI_USE_VERTEXAI=True
   GOOGLE_CLOUD_PROJECT=your-gcp-project-id
   GOOGLE_CLOUD_LOCATION=global
   ```

---

## Usage

### 1. Command Line Interface (CLI)

Run the autonomous agent directly from the terminal to output a test plan file:

```bash
python -m test_planner_agent.main --url https://healthspan.assurecraft.org --prd test_planner_agent/prd_sample.md
```

This will run the workflow and write a production-ready test plan to `test_plan.md`.

### 2. Web UI Dashboard

Start the FastAPI application server locally:

```bash
python -m test_planner_agent.app
```

The web server will run on `http://localhost:8080`. Open this address in your browser to view the interactive, dark-mode glassmorphic TestMind dashboard.

---

## Testing & Validation

TestMind includes unit and integration tests written using `pytest`.

```bash
# Run all tests
pytest
```

- **`tests/test_crawler.py`**: Verifies DOM parsing and interactive element extraction logic.
- **`tests/test_agent.py`**: Asserts the structural integrity of the ADK 2.0 `Workflow` graph.

---

## Cloud Deployment (Docker)

A lightweight `Dockerfile` is provided for containerized deployment on GCP Cloud Run:

```bash
# Build the image
docker build -t test-planning-agent .

# Run the container locally
docker run -p 8080:8080 --env-file .env test-planning-agent
```

---

## License & Citation

### License
This project is licensed under the **Creative Commons Attribution 4.0 International** (CC BY 4.0) License.

### Citation
```bibtex
@misc{chan2026testmind,
  author       = {Fred Chan},
  title        = {TestMind: Agentic Test Planning with Google ADK 2.0},
  year         = {2026},
  howpublished = {\url{https://www.kaggle.com/competitions/vibe-coding-capstone-project/writeups/testmind-agentic-test-planning-with-google-adk-2}}
}
```
