from fastapi import FastAPI, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import asyncio
from web_scraper import scraper
from quiz_parser import quiz_parser
from data_processor import data_processor
from answer_submitter import answer_submitter
from quiz_solver import quiz_solver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LLM Analysis Quiz API", version="1.0.0")

student_secrets = {
    "23f2000595@ds.study.iitm.ac.in": "google_baba25"
}

class QuizRequest(BaseModel):
    email: str
    secret: str
    url: str

class QuizChainRequest(BaseModel):
    email: str
    secret: str
    url: str
    max_questions: Optional[int] = 10

class QuizResponse(BaseModel):
    status: str
    message: str
    url: Optional[str] = None
    content_preview: Optional[str] = None
    instructions: Optional[Dict[str, Any]] = None
    processing_result: Optional[Dict[str, Any]] = None
    submission_result: Optional[Dict[str, Any]] = None
    next_url: Optional[str] = None

class QuizChainResponse(BaseModel):
    status: str
    message: str
    chain_result: Optional[Dict[str, Any]] = None

@app.get("/")
async def root():
    return {"message": "LLM Analysis Quiz API is running"}

@app.post("/quiz", response_model=QuizResponse)
async def start_quiz(request: QuizRequest, background_tasks: BackgroundTasks):
    if not request.email.strip() or not request.secret.strip() or not request.url.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required fields"
        )
    
    if request.email not in student_secrets:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not registered"
        )
    
    if student_secrets[request.email] != request.secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid secret"
        )
    
    logger.info(f"Scraping URL: {request.url}")
    
    html_content, error = await scraper.scrape_page(request.url)
    
    if error:
        logger.error(f"Scraping failed: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch quiz page: {error}"
        )
    
    # Parse quiz instructions
    instructions = quiz_parser.parse_quiz_instructions(html_content)
    
    # Process the quiz task to generate an answer
    processing_result = await data_processor.process_quiz_task(instructions)
    
    # Submit the answer if we have one and a submit URL
    submission_result = None
    next_url = None
    
    if (processing_result.get('answer') is not None and 
        instructions.get('submit_url') is not None):
        
        submission_result = await answer_submitter.submit_answer(
            submit_url=instructions['submit_url'],
            email=request.email,
            secret=request.secret,
            quiz_url=request.url,
            answer=processing_result['answer']
        )
        
        # Extract next URL from submission result
        next_url = submission_result.get('next_url')
    
    content_preview = html_content[:200] + "..." if len(html_content) > 200 else html_content
    
    logger.info(f"Successfully processed quiz task")
    
    return QuizResponse(
        status="success",
        message="Quiz page processed successfully",
        url=request.url,
        content_preview=content_preview,
        instructions=instructions,
        processing_result=processing_result,
        submission_result=submission_result,
        next_url=next_url
    )

@app.post("/quiz-chain", response_model=QuizChainResponse)
async def solve_quiz_chain(request: QuizChainRequest):
    """Solve a chain of quiz questions automatically"""
    if not request.email.strip() or not request.secret.strip() or not request.url.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required fields"
        )
    
    if request.email not in student_secrets:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not registered"
        )
    
    if student_secrets[request.email] != request.secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid secret"
        )
    
    logger.info(f"Starting quiz chain from: {request.url}")
    
    # Solve the entire quiz chain
    chain_result = await quiz_solver.solve_quiz_chain(
        start_url=request.url,
        email=request.email,
        secret=request.secret
    )
    
    return QuizChainResponse(
        status="success",
        message=f"Quiz chain completed: {chain_result['correct_answers']}/{chain_result['total_questions']} correct",
        chain_result=chain_result
    )

@app.on_event("shutdown")
async def shutdown_event():
    await scraper.close()
    await data_processor.close()
    await answer_submitter.close()