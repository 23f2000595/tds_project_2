from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="LLM Analysis Quiz API", version="1.0.0")

class QuizRequest(BaseModel):
    email: str
    secret: str
    url: str

class QuizResponse(BaseModel):
    status: str
    message: str
    url: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "LLM Analysis Quiz API is running"}

@app.post("/quiz")
async def start_quiz(request: QuizRequest):
    print(f"Received quiz request for: {request.email}")
    print(f"URL to process: {request.url}")
    
    # Basic validation
    if not request.email or not request.secret or not request.url:
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    return QuizResponse(
        status="success",
        message="Quiz request received successfully",
        url=request.url
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)