import os
import argparse
import asyncio
import json
import logging
import sys
from typing import Optional
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.genai import types

from test_planner_agent.agent import app as adk_app
from test_planner_agent.config import DEFAULT_SUT_URL
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

async def run_agent_cli(url: str, prd_path: Optional[str]):
    # Setup logging to console
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    
    # Avoid console encoding issues
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        
    print(f"--- Starting Test-Planning Agent CLI ---")
    print(f"Target SUT URL: {url}")
    
    prd_content = ""
    if prd_path:
        if os.path.exists(prd_path):
            with open(prd_path, "r", encoding="utf-8") as f:
                prd_content = f.read()
            print(f"Loaded SUT PRD from: {prd_path}")
        else:
            print(f"PRD file not found at: {prd_path}", file=sys.stderr)
            sys.exit(1)
            
    # Initialize services
    session_service = InMemorySessionService()
    artifact_service = InMemoryArtifactService()
    runner = Runner(
        app=adk_app,
        session_service=session_service,
        artifact_service=artifact_service,
    )
    
    # Create session
    session = await session_service.create_session(
        app_name=adk_app.name,
        user_id="cli_user"
    )
    
    # Formulate inputs
    payload = {
        "url": url,
        "prd": prd_content
    }
    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=json.dumps(payload))]
    )
    
    # Configure artifact output folder (local directory)
    session.state["artifact_dir"] = os.getcwd()
    
    print("\nExecuting graph workflow nodes...")
    
    async for event in runner.run_async(
        user_id="cli_user",
        session_id=session.id,
        new_message=content
    ):
        node_name = event.node_info.path.split("/")[-1] if event.node_info else "System"
        print(f" > [{node_name}] executing/complete")
        
    # Retrieve final state
    final_session = await session_service.get_session(
        app_name=adk_app.name,
        session_id=session.id,
        user_id="cli_user"
    )
    
    plan = final_session.state.get("test_plan_markdown", "")
    if plan:
        print("\n--- Test Plan Generated Successfully! ---")
        print(f"Saved to: {os.path.join(os.getcwd(), 'test_plan.md')}")
        print("\nPreview of first 500 characters:")
        print(plan[:500] + "...\n")
    else:
        print("\nError: Workflow finished but no test plan was generated in the session state.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test-Planning Agent CLI (ADK 2.0)")
    parser.add_argument("--url", default=DEFAULT_SUT_URL, help="The SUT URL to explore and audit")
    parser.add_argument("--prd", help="Path to the PRD file (markdown)")
    args = parser.parse_args()
    
    from typing import Optional
    asyncio.run(run_agent_cli(args.url, args.prd))
