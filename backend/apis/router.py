from typing import TypedDict, Annotated
from langchain_core.agents import AgentAction
from langchain_core.messages import BaseMessage
import operator
from langgraph.graph import StateGraph, END
from apis.rag import rag_search
from apis.arxiv import search_arxiv
from apis.web import search_node
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from langgraph.checkpoint.memory import MemorySaver
import logging

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize MemorySaver
memory_saver = MemorySaver()

# Load environment variables
load_dotenv()

# Define AgentState
class AgentState(TypedDict):
    input: str
    chat_history: list[BaseMessage]
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]

# Function to create scratchpad
def create_scratchpad(intermediate_steps: list[AgentAction]):
    research_steps = []
    for action in intermediate_steps:
        if action.log != "TBD":
            research_steps.append(
                f"Tool: {action.tool}, input: {action.tool_input}\n"
                f"Output: {action.log}"
            )
    return "\n---\n".join(research_steps)

# Error Handling Node
def error_handler(state):
    error_message = state.get("error", "An unexpected error occurred.")
    logger.error(f"Error encountered: {error_message}")
    state["messages"].append({"content": f"Error: {error_message}"})
    return "final_answer"  # Route to final answer after handling the error

# Oracle function with MemorySaver integration
async def oracle(state):
    try:
        state = memory_saver.load(state)  # Restore state
        input = state["messages"][-1]["content"]

        intermediate_steps = state.get("intermediate_steps", [])

        if "RAG" in input:
            decision = "rag_search"
        elif "web" in input:
            decision = "web_search"
        else:
            decision = "arxiv_search"

        scratchpad = create_scratchpad(intermediate_steps)

        memory_saver.save(state)  # Save updated state
        return {"decision": decision, "scratchpad": scratchpad}
    except Exception as e:
        logger.error(f"Oracle Error: {str(e)}")
        state["error"] = str(e)
        return state

# Initialize the graph with AgentState
graph = StateGraph(AgentState)

# Define the entry point node
graph.add_node("check_initial_state", lambda state: {"messages": state["messages"]})

# Define nodes for the main workflow
graph.add_node("oracle", oracle)
graph.add_node("arxiv_search", search_arxiv)
graph.add_node("rag_search", rag_search)
graph.add_node("web_search", search_node)
graph.add_node("final_answer", lambda state: {"messages": state["messages"]})
graph.add_node("error_handler", error_handler)

# Set the entry point to check initial state
graph.set_entry_point("check_initial_state")

# Check initial state function
def check_initial_state(state):
    if not state.get("messages"):
        state["messages"] = [{"content": "Initializing chat..."}]
    memory_saver.save(state)
    return "oracle"

# Updated router function with error handling integration
def router(state):
    try:
        decision = state.get("decision", "").lower()
        intermediate_steps = state.get("intermediate_steps", [])
        resources = state.get("resources", [])

        # Fallback if Arxiv search or Web search yields no results
        if decision == "arxiv_search" and not resources:
            return "web_search"
        if decision == "web_search" and not resources:
            return "final_answer"  # Exit if no results after Web search

        # Handle summary request, route to RAG search
        if "summary" in state["messages"][-1]["content"].lower():
            return "rag_search"

        # Default routing based on the decision
        if decision == "arxiv_search":
            return "arxiv_search"
        elif decision == "rag_search":
            return "rag_search"
        elif decision == "web_search":
            return "web_search"
        elif decision == "final_answer":
            return "final_answer"
        else:
            return "oracle"
    except Exception as e:
        logger.error(f"Router Error: {str(e)}")
        state["error"] = str(e)
        return "error_handler"

# Define conditional edges with error handling integration
graph.add_conditional_edges(source="check_initial_state", path=lambda state: "oracle")
graph.add_conditional_edges(source="oracle", path=router)

# Loop back tool nodes to Oracle for further decisions and error handling
for tool_name in ["arxiv_search", "rag_search", "web_search"]:
    graph.add_edge(tool_name, "oracle")
    graph.add_edge(tool_name, "error_handler")

# Direct edge from RAG search to final answer if summary is requested
graph.add_edge("rag_search", "final_answer")

# Exit condition for web and arxiv search to final answer
graph.add_edge("web_search", "final_answer")
graph.add_edge("arxiv_search", "final_answer")

# Edge to error handler for unhandled errors
graph.add_edge("oracle", "error_handler")

# Edge to final answer node, then to END
graph.add_edge("final_answer", END)

# Compile the graph
workflow = graph.compile()

# Initialize the LLM
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    OPENAI_API_KEY=os.getenv("OPENAI_API_KEY"),
    temperature=0
)

# List of tools
tools = [
    rag_search,
    search_arxiv,
    search_node,
    lambda state: {"message": "Final answer gathered from all sources."}
]

for tool in tools:
    print(f"Tool Name: {tool.__name__}")
    print(f"Function Annotations: {tool.__annotations__}")
    print(f"Docstring: {tool.__doc__}")




# Bind tools to the LLM
llm.bind_tools(tools, tool_choice="any")
