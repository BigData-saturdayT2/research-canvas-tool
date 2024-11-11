import requests
import xmltodict
from langchain_core.tools import tool
import logging

logger = logging.getLogger(__name__)

ARXIV_API_URL = "http://export.arxiv.org/api/query"

@tool("search_arxiv")
def search_arxiv(query: str) -> dict:
    """
    Searches for research papers on Arxiv based on the provided query.
    
    Args:
        query (str): The search term or topic to look up.
    
    Returns:
        dict: A dictionary containing either the search results or an error message.
    """
    try:
        # Configure the search parameters
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": 5,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }

        # Send request to Arxiv API
        response = requests.get(ARXIV_API_URL, params=params)
        
        if response.status_code != 200:
            return {"error": f"Failed to fetch data from Arxiv. Status code: {response.status_code}"}

        # Parse the XML response
        data = xmltodict.parse(response.text)
        
        # Check if we have any entries
        entries = data.get('feed', {}).get('entry', [])
        
        # If there's only one entry, wrap it in a list
        if isinstance(entries, dict):
            entries = [entries]
            
        results = []
        
        for entry in entries:
            # Handle authors - could be single author or list
            authors = entry.get('author', [])
            if isinstance(authors, dict):
                authors = [authors]
            
            author_names = [author.get('name', '') for author in authors]
            
            # Extract other paper details
            paper = {
                "title": entry.get('title', '').replace('\n', ' ').strip(),
                "summary": entry.get('summary', '').replace('\n', ' ').strip(),
                "authors": author_names,
                "published": entry.get('published', ''),
                "link": entry.get('id', ''),
                "pdf_url": next((link.get('@href', '') 
                               for link in entry.get('link', []) 
                               if isinstance(link, dict) and link.get('@title') == 'pdf'), 
                              None)
            }
            results.append(paper)
            
        if not results:
            return {"message": "No papers found matching your query."}
            
        return {"results": results}

    except Exception as e:
        logger.error(f"Error in search_arxiv: {str(e)}")
        return {"error": f"An error occurred while searching: {str(e)}"}