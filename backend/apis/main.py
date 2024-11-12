from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
import uvicorn
from apis.router import workflow
from langgraph.checkpoint.memory import MemorySaver
import logging

# Initialize FastAPI app and MemorySaver
app = FastAPI()
memory_saver = MemorySaver()
logger = logging.getLogger(__name__)

# Request model for input data
class UserRequest(BaseModel):
    input: str
    state: Dict = {}

# Endpoint for user input
@app.post("/input")
async def input(request: UserRequest):
    try:
        # Load the state from the request or initialize it
        state = request.state or {}
        state["input"] = request.input

        # Restore state using MemorySaver
        state = memory_saver.load(state)

        # Process the input using the compiled workflow
        result_state = await workflow(state)

        # Save the updated state
        memory_saver.save(result_state)

        # Return the final messages from the state
        return {"messages": result_state.get("messages", [])}
    except Exception as e:
        logger.error(f"input Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Root endpoint for health check
@app.get("/")
def root():
    return {"message": "LangGraph Agent API is running"}

# Run FastAPI server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
