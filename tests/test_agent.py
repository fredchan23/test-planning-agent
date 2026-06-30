import pytest
from test_planner_agent.agent import app as adk_app
from google.adk.workflow import Workflow

def test_workflow_structure():
    assert adk_app.name == "test_planner_agent"
    assert isinstance(adk_app.root_agent, Workflow)
    assert adk_app.root_agent.name == "root_agent"
    
    # Verify graph contains nodes
    # START -> parse_input -> run_crawler -> intent_mapper -> scenario_matrix_agent -> element_grounding_agent -> compile_output
    edges = adk_app.root_agent.edges
    assert len(edges) > 0
