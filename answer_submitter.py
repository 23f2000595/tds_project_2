import httpx
import json
import logging
from typing import Dict, Any, Optional
import asyncio

logger = logging.getLogger(__name__)

class AnswerSubmitter:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def submit_answer(self, 
                          submit_url: str, 
                          email: str, 
                          secret: str, 
                          quiz_url: str, 
                          answer: Any) -> Dict[str, Any]:
        """
        Submit answer to the evaluation endpoint
        """
        payload = {
            "email": email,
            "secret": secret,
            "url": quiz_url,
            "answer": answer
        }
        
        logger.info(f"Submitting answer to: {submit_url}")
        logger.info(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = await self.client.post(
                submit_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            logger.info(f"Submission response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Submission successful: {result}")
                return {
                    "status": "submitted",
                    "correct": result.get("correct", False),
                    "reason": result.get("reason"),
                    "next_url": result.get("url"),
                    "response": result
                }
            else:
                error_msg = f"Submission failed with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "error": error_msg,
                    "correct": False
                }
                
        except Exception as e:
            error_msg = f"Submission error: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "correct": False
            }
    
    async def close(self):
        await self.client.aclose()

# Global submitter instance
answer_submitter = AnswerSubmitter()