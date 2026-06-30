import os
import json
import logging
from typing import Any, Dict
from google.adk.agents import LlmAgent
from google.adk.workflow import Workflow, START, node
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.agents.context import Context
from google.adk.events.event import Event
from google.genai import types

from test_planner_agent.config import MODEL_NAME, PRD_SAMPLE_PATH, DEFAULT_SUT_URL
from test_planner_agent.crawler import WebCrawler

logger = logging.getLogger(__name__)

# Try to load environment variables from .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

use_vertex = os.environ.get("GOOGLE_GENAI_USE_ENTERPRISE", os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "True")).lower() in ("true", "1", "yes")

if use_vertex:
    os.environ["GOOGLE_GENAI_USE_ENTERPRISE"] = "True"
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
    if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
        try:
            import google.auth
            _, project_id = google.auth.default()
            if project_id:
                os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
        except Exception:
            pass
    # Force global location to avoid regional 404 model errors on Vertex AI
    os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
else:
    os.environ["GOOGLE_GENAI_USE_ENTERPRISE"] = "False"
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"

# Initialize model
gemini_model = Gemini(
    model=MODEL_NAME,
    retry_options=types.HttpRetryOptions(attempts=3),
)

# 1. Parse Input Node
@node
def parse_input(ctx: Context, node_input: Any) -> Event:
    """Parses input URL and optional PRD text. Sets up initial state."""
    logger.info(f"Parsing inputs: {node_input}")
    
    target_url = DEFAULT_SUT_URL
    prd_content = ""
    
    raw_input = None
    if isinstance(node_input, dict):
        raw_input = node_input
    elif isinstance(node_input, str):
        try:
            raw_input = json.loads(node_input)
        except Exception:
            raw_input = node_input
    elif hasattr(node_input, "parts") and node_input.parts:
        text = "".join(part.text for part in node_input.parts if part.text)
        try:
            raw_input = json.loads(text)
        except Exception:
            raw_input = text

    max_depth = 2
    max_pages = 5

    if isinstance(raw_input, dict):
        target_url = raw_input.get("url", DEFAULT_SUT_URL)
        prd_content = raw_input.get("prd", "")
        max_depth = int(raw_input.get("max_depth", 2))
        max_pages = int(raw_input.get("max_pages", 5))
    elif isinstance(raw_input, str):
        if raw_input.startswith("http"):
            target_url = raw_input
        else:
            prd_content = raw_input

    # If SUT is the Singapore Healthspan Simulator and PRD is empty, load default sample
    if "healthspan.assurecraft.org" in target_url and not prd_content:
        if os.path.exists(PRD_SAMPLE_PATH):
            with open(PRD_SAMPLE_PATH, "r", encoding="utf-8") as f:
                prd_content = f.read()
            logger.info("Loaded default SUT PRD from prd_sample.md")
            
    state_delta = {
        "target_url": target_url,
        "prd_content": prd_content or "No PRD provided. Infer intent from crawled DOM.",
        "max_depth": max_depth,
        "max_pages": max_pages,
        "progress": ["Inputs parsed successfully."]
    }

    return Event(output=target_url, state=state_delta)


# 2. Crawler Node
@node
async def run_crawler(ctx: Context, node_input: Any) -> Event:
    """Crawls the SUT and performs DOM static audit."""
    target_url = ctx.state.get("target_url", DEFAULT_SUT_URL)
    logger.info(f"Running crawler against target: {target_url}")
    
    crawler = WebCrawler(target_url, max_depth=2, max_pages=5)
    crawled_data = await crawler.crawl()
    
    # Save a simplified representation for prompts
    simplified_dom = {}
    for path, data in crawled_data.items():
        simplified_dom[path] = {
            "title": data.get("title"),
            "description": data.get("description"),
            "elements": [
                {
                    "name": elem.get("name"),
                    "role": elem.get("role"),
                    "selector": elem.get("selector"),
                    "options": elem.get("options", [])
                }
                for elem in data.get("interactive_elements", [])
            ]
        }
        
    state_delta = {
        "crawled_data": crawled_data,
        "simplified_dom": simplified_dom,
        "progress": ctx.state.get("progress", []) + ["SUT website crawled and DOM audited."]
    }
    
    # Pass the state to the LLM agent next
    llm_payload = {
        "prd": ctx.state.get("prd_content"),
        "dom": simplified_dom
    }
    
    return Event(output=json.dumps(llm_payload), state=state_delta)


# 3. Intent Mapper Node (LlmAgent)
intent_mapper = LlmAgent(
    name="intent_mapper",
    model=gemini_model,
    instruction=(
        "You are a Quality Assurance Architect. Your task is to align the business requirements (PRD) "
        "with the crawled page DOM structure and identify the core business goals, journeys, and checkpoints.\n\n"
        "Input consists of a JSON string with keys:\n"
        "- 'prd': The product requirements.\n"
        "- 'dom': The crawled web pages and interactive controls (accessible role, label, selector).\n\n"
        "Define a clean hierarchy:\n"
        "1. Goals: Top-level business outcomes (e.g., 'Demographic baseline simulation').\n"
        "2. Journeys: E2E user paths from start to outcome.\n"
        "3. Checkpoints: Reusable blocks (e.g., 'Demographics configuration', 'Habits toggle').\n\n"
        "Analyze the inputs and output a comprehensive Journeys map in Markdown format."
    )
)


# 4. Deep Scenario Matrix Agent
scenario_matrix_agent = LlmAgent(
    name="scenario_matrix_agent",
    model=gemini_model,
    instruction=(
        "You are an expert QA Engineer specialized in boundary analysis and risk-based testing.\n\n"
        "Based on the Journeys map generated by the Intent Mapper (provided as input), "
        "infer all potential execution scenarios, categorizing them into:\n"
        "1. Positive Cases (Happy path)\n"
        "2. Negative Scenarios (Sad path / Error handling)\n"
        "3. Boundary & Equivalence splits (e.g. check current_age limits: min 18, max 100)\n"
        "4. Implicit Scenarios (Session redirections, reactive state updates)\n\n"
        "For each scenario, assign a Risk Priority:\n"
        "- Priority 0 (Critical Path): Core flows (e.g., standard male/female calculations, basic result outputs).\n"
        "- Priority 1 (Important Path): High-frequency changes (e.g. lifestyle toggles like smoking/activity, change-ages).\n"
        "- Priority 2 (Secondary Path): Low-risk UI validations, language toggle, explore page sections.\n\n"
        "Output the scenario matrix as a structured Markdown table."
    )
)


# 5. Element Grounding Agent
element_grounding_agent = LlmAgent(
    name="element_grounding_agent",
    model=gemini_model,
    instruction=(
        "You are a Playwright Automation Specialist. Your task is to ground the scenarios "
        "into concrete test steps and elements, and define pre-conditions, synthetic data, and expected outcomes.\n\n"
        "For each test step, reference the stable semantic accessibility markers (Role, Name, selector) "
        "provided in the crawled DOM structure.\n\n"
        "Include:\n"
        "1. Pre-conditions (required session states, cookies, default baselines).\n"
        "2. Synthetic Data Definitions (exact parameters to input, e.g. age=45, sex=female, sleep=poor).\n"
        "3. Declarative Intent Verification (expected outcomes stated in natural language, not hardcoded CSS selectors).\n\n"
        "Also, compile the final Semantic Target Mapping: a JSON map of element keys to their semantic markers and CSS selectors "
        "(e.g., 'sex_male_radio' -> { 'role': 'radio_group', 'name': 'Male', 'selector': 'input[name=\"sex\"]' }).\n\n"
        "Output this combined data in Markdown format."
    )
)


# 6. Output Generator Node
@node
def compile_output(ctx: Context, node_input: Any) -> Event:
    """Compiles results from previous agents and outputs the final Markdown Test Plan."""
    logger.info("Compiling final test plan output...")
    
    # Extract states or LLM responses
    target_url = ctx.state.get("target_url")
    
    # We can retrieve the trace of events to extract LLM answers
    intent_map_res = ""
    scenario_matrix_res = ""
    element_grounding_res = ""
    
    # Traverse events in current session to fetch outputs of the agents
    for event in ctx.session.events:
        if event.node_info:
            node_name = event.node_info.path.split("/")[-1]
            # If the event came from model
            if event.content and event.content.role == "model":
                text = "".join(part.text for part in event.content.parts if part.text)
                if node_name.startswith("intent_mapper"):
                    intent_map_res = text
                elif node_name.startswith("scenario_matrix_agent"):
                    scenario_matrix_res = text
                elif node_name.startswith("element_grounding_agent"):
                    element_grounding_res = text

    # If for some reason trace is not populated (e.g. single node run or direct input), fallback to node_input
    if not element_grounding_res and isinstance(node_input, str):
        element_grounding_res = node_input

    # Parse and compile a beautiful Markdown document
    markdown_plan = f"""# Agentic Test Plan: {target_url}

This comprehensive test plan has been generated dynamically by the ADK 2.0 Test-Planning Agent. It outlines the hierarchical user journeys, a deep scenario matrix, risk-based priorities, and semantic locators grounded in the web accessibility tree.

---

## 1. Hierarchical Journey Mapping

{intent_map_res or "Pending generation"}

---

## 2. Deep Scenario Matrix (Happy, Sad, and Edge Paths)

{scenario_matrix_res or "Pending generation"}

---

## 3. Element Grounding & Fixture Prerequisites

{element_grounding_res or "Pending generation"}

---

## 4. Semantic Target Mapping

Below is the mapping between logical elements used in the assertions and their stable DOM selectors:

| Element Key | Role | Display Name | CSS/XPath Selector |
| :--- | :--- | :--- | :--- |
"""
    
    # Extract element mappings dynamically from the crawled data to embed them as a fallback table
    crawled_data = ctx.state.get("crawled_data", {})
    mapping_dict = {}
    
    for path, data in crawled_data.items():
        for elem in data.get("interactive_elements", []):
            name = elem.get("name")
            role = elem.get("role")
            selector = elem.get("selector")
            html_name = elem.get("html_name") or name.lower().replace(" ", "_")
            
            mapping_dict[html_name] = {
                "role": role,
                "name": name,
                "selector": selector,
                "path": path
            }
            
            markdown_plan += f"| `{html_name}` | `{role}` | **{name}** | `{selector}` |\n"
            
    # Also attempt to extract grounded mappings from the LLM element_grounding_res response
    import re
    llm_mapping = {}
    if element_grounding_res:
        json_matches = re.findall(r"```json\s*(\{.*?\})\s*```", element_grounding_res, re.DOTALL)
        for match_text in json_matches:
            try:
                parsed_json = json.loads(match_text)
                if isinstance(parsed_json, dict):
                    for k, v in parsed_json.items():
                        if isinstance(v, dict):
                            llm_mapping[k] = {
                                "role": v.get("role", "element"),
                                "name": v.get("name", k),
                                "selector": v.get("selector", ""),
                                "path": v.get("path", "")
                            }
                        elif isinstance(v, str):
                            llm_mapping[k] = {
                                "role": "element",
                                "name": k,
                                "selector": v,
                                "path": ""
                            }
            except Exception as ex:
                logger.warning(f"Failed to parse target mapping JSON from LLM: {ex}")

    # Merge crawler-discovered targets with LLM-grounded targets
    final_mapping = {**mapping_dict, **llm_mapping}

    # Also embed raw JSON for generator agent ingestion
    markdown_plan += f"\n### Structured JSON Hand-Off\n```json\n{json.dumps(final_mapping, indent=2)}\n```\n"

    # Save to artifacts directory (scoped within current conversation)
    artifact_dir = ctx.state.get("artifact_dir", ".")
    test_plan_path = os.path.join(artifact_dir, "test_plan.md")
    
    try:
        # Attempt to write local file
        os.makedirs(os.path.dirname(os.path.abspath(test_plan_path)), exist_ok=True)
        with open(test_plan_path, "w", encoding="utf-8") as f:
            f.write(markdown_plan)
        logger.info(f"Test plan written to {test_plan_path}")
    except Exception as e:
        logger.error(f"Failed to write test plan artifact: {e}")

    state_delta = {
        "test_plan_markdown": markdown_plan,
        "semantic_target_mapping": final_mapping,
        "progress": ctx.state.get("progress", []) + ["Test plan generated and saved as artifact."]
    }
    
    return Event(
        output=markdown_plan,
        state=state_delta,
        content=types.Content(
            role="model",
            parts=[types.Part.from_text(text=f"✅ **Test Plan Compiled Successfully**!\n\nPreviewing generated test plan:\n\n{markdown_plan[:800]}...\n\nFind full plan at `test_plan.md` in the artifacts.")],
        )
    )


# 7. Workflow Definition
root_agent = Workflow(
    name="root_agent",
    edges=[
        (START, parse_input),
        (parse_input, run_crawler),
        (run_crawler, intent_mapper),
        (intent_mapper, scenario_matrix_agent),
        (scenario_matrix_agent, element_grounding_agent),
        (element_grounding_agent, compile_output),
    ],
)

app = App(
    root_agent=root_agent,
    name="test_planner_agent",
)
