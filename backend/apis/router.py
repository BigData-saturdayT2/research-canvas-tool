from apis.arxiv import search_arxiv
from langgraph.prebuilt import ToolNode

# Define the tools for the agent
tools = [search_arxiv]

# Create a ToolNode for integrating the Arxiv tool
tool_node = ToolNode(tools)
