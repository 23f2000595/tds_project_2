from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import httpx
import json
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LLM Analysis Quiz API", version="1.0.0")

# Request models
class QuizRequest(BaseModel):
    email: str
    secret: str
    url: str

class QuizResponse(BaseModel):
    email: str
    secret: str
    url: str
    answer: Optional[Any] = None

# In-memory storage for secrets (replace with database in production)
USER_SECRETS = {}

@app.post("/api/quiz")
async def process_quiz(request: QuizRequest):
    """Process quiz task from provided URL"""
    
    # Verify secret
    if request.secret not in USER_SECRETS.values():
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    logger.info(f"Processing quiz for {request.email} at {request.url}")
    
    try:
        # Here you would integrate with your quiz solver
        # For now, return a placeholder response
        response = {
            "email": request.email,
            "secret": request.secret, 
            "url": request.url,
            "answer": None,
            "status": "processed"
        }
        return response
        
    except Exception as e:
        logger.error(f"Error processing quiz: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/")
async def root():
    return {"message": "LLM Analysis Quiz API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
