import os
from dotenv import load_dotenv
import requests
import logging
from openai import OpenAI
from pinecone import Pinecone  # Correct import for Pinecone v3.0+
from langchain_pinecone import Pinecone as PineconeVectorStore  # Correct import for LangChain Pinecone
from langchain.embeddings.huggingface import HuggingFaceEmbeddings  # Correct import for HuggingFace embeddings

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()
logging.info("Loaded environment variables from .env file.")

# Initialize Pinecone client using the new object-oriented approach (v3.0+)
api_key = os.getenv("PINECONE_API_KEY")
if not api_key:
    logging.error("PINECONE_API_KEY is not set in the environment variables.")
    raise ValueError("PINECONE_API_KEY is missing.")
else:
    logging.info("Pinecone API key loaded successfully.")

pc = Pinecone(api_key=api_key)
logging.info("Initialized Pinecone client.")

# Define index name
index_name = "index-f5e83a5988b93179f774fa79002beb34"
logging.info(f"Using index name: {index_name}")

# Check if index exists, if not, create it
if index_name not in pc.list_indexes().names():
    logging.info(f"Index '{index_name}' does not exist. Creating a new index...")
    pc.create_index(
        name=index_name,
        dimension=384,
        metric='cosine'
    )
    logging.info(f"Index '{index_name}' created successfully.")
else:
    logging.info(f"Index '{index_name}' already exists.")

# Connect to the existing Pinecone index
index = pc.Index(index_name)
logging.info(f"Connected to Pinecone index: {index_name}")

# Load embeddings (use HuggingFace embeddings for compatibility with Mistral or other LLMs)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
logging.info("HuggingFace embeddings model loaded: sentence-transformers/all-MiniLM-L6-v2")

# Initialize LangChain's Pinecone vector store (pass the Embeddings object directly)
vector_store = PineconeVectorStore(index=index, embedding=embeddings)
logging.info("Initialized LangChain's Pinecone vector store.")

# Create a retriever using the vector store's as_retriever method
retriever = vector_store.as_retriever()
logging.info("Retriever created from the vector store.")

nvidia_api_key = os.getenv("NVIDIA_API_KEY")
if not nvidia_api_key:
    logging.error("NVIDIA_API_KEY is not set in the environment variables.")
    raise ValueError("NVIDIA_API_KEY is missing.")
else:
    logging.info("NVIDIA API key loaded successfully.")

nvidia_api_url = "https://integrate.api.nvidia.com/v1"
nvidia_model_name = "meta/llama3-8b-instruct"  # Updated model name

# Initialize the NVIDIA client using OpenAI's interface
client = OpenAI(
    base_url=nvidia_api_url,
    api_key=nvidia_api_key
)

def call_nvidia_llama_api(prompt: str) -> dict:
    """
    Sends a prompt to the NVIDIA Llama3-8B-Instruct API and retrieves a response.

    Args:
        prompt (str): The input prompt for the Llama3-8B-Instruct model.

    Returns:
        dict: The generated response from Llama3-8B-Instruct.
    """
    logging.info(f"Calling NVIDIA Llama3 API with prompt: {prompt[:50]}...")  # Log only first 50 chars of prompt

    try:
        completion = client.chat.completions.create(
            model=nvidia_model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200
        )

        # Return the response from the API
        return completion

    except Exception as e:
        logging.error(f"Failed to call NVIDIA API: {str(e)}")
        return {"error": str(e)}

def rag_search(query: str) -> dict:
    """
    Retrieves relevant documents from Pinecone based on the query and generates a response using NVIDIA Llama3-8B-Instruct API.

    Args:
        query (str): The user's query.

    Returns:
        dict: The generated response from Llama3-8B-Instruct.
    """
    logging.info(f"Performing RAG search for query: {query}")

    # Retrieve relevant documents from Pinecone based on query
    relevant_docs = retriever.get_relevant_documents(query)
    
    if relevant_docs:
        logging.info(f"Retrieved {len(relevant_docs)} relevant documents from Pinecone.")
    else:
        logging.warning("No relevant documents found for the query.")

    # Prepare prompt by combining query and retrieved documents' content
    # For simplicity, we are only using the query in this example.
    
    prompt = f"Query: {query}"
    
    # Call NVIDIA Llama3-8B-Instruct API to generate a response based on the combined prompt
    llama_response = call_nvidia_llama_api(prompt)

    return llama_response

# # Example usage:
# query = "What is the capital of France?"
# response = rag_search(query)
# print(response)