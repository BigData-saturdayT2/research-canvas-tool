import os
from typing import List
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage
from langchain.tools import tool
from tavily import TavilyClient
from copilotkit.langchain import copilotkit_emit_state
import logging

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Define the structure for resource input (reuse with flexibility)
class ResourceInput(BaseModel):
    """A resource with a short description"""
    url: str = Field(description="The URL of the resource")
    title: str = Field(description="The title of the resource")
    description: str = Field(description="A short description of the resource")

# Define a search tool that extracts top resources from search results
@tool
def ExtractTopResources(resources: List[ResourceInput]):
    """Extract the 3-5 most relevant resources from a search result."""
    logger.info("Extracting top resources from search results")
    return sorted(resources, key=lambda x: x.title)[:5]  # Example sorting strategy, can be customized

# Setup the Tavily client (API key for web searches)
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

async def search_node(input: str, state: dict, config: dict) -> dict:
    """
    The search node handles internet searches based on user queries.
    It gathers resources and updates the state with the findings.
    """
    logger.info("Starting search node")

    # Check if messages exist in state
    if not state.get("messages"):
        logger.error("No messages in state.")
        return {"error": "No messages in state."}  # Early return if no messages

    # Log the incoming state (whole message structure)
    ai_message = state["messages"][-1]
    logger.debug(f"AI Message: {ai_message}")  # Log the full message to inspect the structure

    # Assuming input is in the 'content' key of the message
    user_input = ai_message.get("content", "")
    if not user_input:
        logger.error("No input found in the message content.")
        return {"error": "No input found in the message content"}

    logger.info(f"Received input: {user_input}")

    # Initialize search logs and resources in state if not present
    state["resources"] = state.get("resources", [])
    state["logs"] = state.get("logs", [])

    # Perform search for the input using Tavily
    logger.info(f"Performing search for input: {user_input}")
    try:
        search_response = tavily_client.search(user_input)
        state["resources"].append(search_response)
        logger.info(f"Search results for input '{user_input}' fetched successfully.")
    except Exception as e:
        logger.error(f"Error performing search for input '{user_input}': {str(e)}")
        state["logs"].append({"message": f"Error performing search for '{user_input}'", "done": True})

    # Add a log entry after fetching search results
    state["logs"].append({"message": f"Search results for '{user_input}' fetched.", "done": True})

    # Update the state with search results
    logger.debug("Updating state with search results")
    await copilotkit_emit_state(config, state)

    # Return the updated state with results
    logger.info(f"Resources added: {state['resources']}")
    state["messages"].append({"content": f"Added the following resources: {state['resources']}"})
    logger.debug(f"Final state: {state['messages']}")

    return state


