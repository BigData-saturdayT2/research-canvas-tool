# main.py

from fastapi import FastAPI
from copilotkit import CopilotKitSDK, LangGraphAgent
from langgraph.graph import StateGraph, START, END, MessagesState
from apis.rag import rag_search
from apis.arxiv import search_arxiv
from apis.router import tool_node  # Updated router with both Arxiv and RAG tools
import logging

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define state graph using MessagesState
state_graph = StateGraph(MessagesState)

# selector function that decides whether to use Arxiv or RAG based on query content.
def selector(state: MessagesState) -> str:
    last_message = state["messages"][-1].content.lower()
    
    if "arxiv" in last_message:
        return "fetch_arxiv"
    
    if "rag" in last_message:
        return "rag_search"
    
    return "finalAnswer"

# Add nodes and edges to state graph based on architecture diagram.
state_graph.add_node("selector", selector)
state_graph.add_node("fetch_arxiv", tool_node)  # Run Arxiv search if selected by selector.
state_graph.add_node("rag_search", tool_node)  # Run RAG search if selected by selector.
state_graph.add_node("finalAnswer", lambda state: {"messages": state["messages"]})

state_graph.add_edge(START, "selector")
state_graph.add_edge("selector", "fetch_arxiv")
state_graph.add_edge("selector", "rag_search")
state_graph.add_edge("selector", "finalAnswer")
state_graph.add_edge("fetch_arxiv", "finalAnswer")
state_graph.add_edge("rag_search", "finalAnswer")

# Compile workflow into runnable graph.
workflow = state_graph.compile()

# Initialize CopilotKit SDK with LangGraphAgent.
sdk = CopilotKitSDK(
    agents=[LangGraphAgent(
        name="combined_agent",
        description="An agent that searches for research papers using Arxiv or retrieves documents using RAG.",
        graph=workflow,
    )]
)

@app.post("/rag-search")
async def rag_search_endpoint(payload: dict[str, str]):
    """
    Endpoint to handle RAG search queries.
    
    Args:
        payload (dict): A dictionary containing the user's query.

    Returns:
        dict: The response from the RAG search process.
    """
    query = payload.get("query", "")
    
    if not query:
        return {"error": "No query provided"}
    
    try:
        # Call the rag_search function and return its result
        response = rag_search(query)
        return response
    
    except Exception as e:
        return {"error": str(e)}

@app.post("/copilotkit_remote")
async def handle_copilotkit_remote(payload: dict):
    try:
        logger.info(f"Received payload: {payload}")
        
        # Extract query from the payload
        user_query = payload.get('messages', [{}])[0].get('content', '')
        logger.info(f"Running agent with payload: {user_query}")
        
        # Check if query is not empty
        if user_query:
            logger.info(f"Searching for papers related to: {user_query}")
            
            # Use the invoke method as recommended
            search_results = search_arxiv.invoke(user_query)
            
            logger.info(f"Search results returned: {search_results}")
            return search_results  # Return the results directly
        
        else:
            logger.error("No query provided in the payload.")
            return {"error": "No query provided"}
    
    except Exception as e:
        logger.error(f"Error invoking Arxiv tool: {str(e)}")
        return {"error": str(e)}

@app.get("/")
def read_root():
    return {"message": "Hello from Combined Agent!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)