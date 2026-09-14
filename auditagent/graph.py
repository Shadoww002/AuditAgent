import operator
from typing import Annotated, Sequence, TypedDict

from langgraph.graph import StateGraph, END
from auditagent.state import AuditState

# Import nodes
from auditagent.agents.planner import planner_node
from auditagent.agents.workers.dependency import dependency_agent_node
from auditagent.agents.workers.secrets import secrets_agent_node
from auditagent.agents.critic import critic_agent_node
from auditagent.agents.writer import writer_agent_node

# To merge lists properly in LangGraph state, we need to define a reducer
def reduce_list(left: list | None, right: list | None) -> list:
    if not left:
        left = []
    if not right:
        right = []
    return left + right

# Create a TypedDict version of AuditState for LangGraph to handle updates easily
class GraphState(TypedDict):
    repository_path: str
    metadata: dict
    findings: Annotated[list, reduce_list]
    verified_findings: Annotated[list, reduce_list]
    final_report: str
    errors: Annotated[list, reduce_list]

def build_graph() -> StateGraph:
    """
    Builds the LangGraph directed graph for the AuditAgent workflow.
    """
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("dependency_agent", dependency_agent_node)
    workflow.add_node("secrets_agent", secrets_agent_node)
    workflow.add_node("critic", critic_agent_node)
    workflow.add_node("writer", writer_agent_node)
    
    # Define edges
    # Intake -> Planner
    workflow.set_entry_point("planner")
    
    # Planner -> Workers (Parallel)
    workflow.add_edge("planner", "dependency_agent")
    workflow.add_edge("planner", "secrets_agent")
    
    # Workers -> Critic
    # We need the critic to wait for both workers. LangGraph handles this naturally
    # when multiple nodes point to a single node, they join.
    workflow.add_edge("dependency_agent", "critic")
    workflow.add_edge("secrets_agent", "critic")
    
    # Critic -> Writer
    workflow.add_edge("critic", "writer")
    
    # Writer -> End
    workflow.add_edge("writer", END)
    
    return workflow.compile()
