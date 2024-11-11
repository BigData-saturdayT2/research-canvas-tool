from fastapi import FastAPI
from copilotkit import CopilotKitSDK, LangGraphAgent
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from apis.router import tool_node
import logging
from apis.arxiv import search_arxiv  # Import the search_arxiv function

# Initialize FastAPI app
app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the state using MessagesState
state_graph = StateGraph(MessagesState)

# Define a simple function for model invocation (placeholder)
def call_model(state: MessagesState):
    user_query = state["messages"][-1].content  # Extract the user's query
    logger.info(f"Received query: {user_query}")
    
    # Generate a response based on the query
    new_message = {"role": "assistant", "content": f"Received query: {user_query}"}
    state["messages"].append(new_message)  # Append to the state messages
    return {"messages": state["messages"]}

# Define the function that determines whether to continue or end
def should_continue(state: MessagesState) -> str:
    last_message = state["messages"][-1]
    if "search" in last_message.content.lower():
        return "tools"  # Route to tools if 'search' is in the message
    return END  # End the process if no search is found

# Add nodes to the graph
state_graph.add_node("agent", call_model)
state_graph.add_node("tools", tool_node)

# Define workflow edges
state_graph.add_edge(START, "agent")
state_graph.add_conditional_edges("agent", should_continue)
state_graph.add_edge("tools", "agent")

# Compile the graph into a runnable workflow
workflow = state_graph.compile()

# Initialize the CopilotKit SDK with LangGraphAgent
sdk = CopilotKitSDK(
    agents=[LangGraphAgent(
        name="arxiv_agent",
        description="An agent that searches for research papers using the Arxiv API.",
        graph=workflow
    )]
)

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
    return {"message": "Hello, World from FastAPI!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)