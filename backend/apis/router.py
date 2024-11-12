# router.py
from apis.arxiv import search_arxiv
from apis.rag import rag_search  # Import RAG search function
from langgraph.prebuilt import ToolNode

# Define the tools for the agent (both Arxiv and RAG)
tools = [rag_search]

# Create a ToolNode for integrating both tools
tool_node = ToolNode(tools)