import logging
import asyncio
from typing import Dict, Any, List, Optional
from web_scraper import scraper
from quiz_parser import quiz_parser
from data_processor import data_processor
from answer_submitter import answer_submitter

logger = logging.getLogger(__name__)

class QuizSolver:
    def __init__(self):
        self.visited_urls = set()
        self.max_attempts = 10  # Prevent infinite loops
    
    async def solve_quiz_chain(self, start_url: str, email: str, secret: str) -> Dict[str, Any]:
        """
        Solve a chain of quiz questions automatically - OPTIMIZED FOR SPEED
        """
        current_url = start_url
        results = {
            'start_url': start_url,
            'completed': False,
            'total_questions': 0,
            'correct_answers': 0,
            'chain': []
        }
        
        attempt = 0
        
        while current_url and attempt < self.max_attempts:
            attempt += 1
            
            if current_url in self.visited_urls:
                logger.warning(f"Already visited URL: {current_url}")
                break
                
            self.visited_urls.add(current_url)
            results['total_questions'] += 1
            
            logger.info(f"Solving quiz #{attempt}: {current_url}")
            
            # Process current quiz with timeout
            try:
                quiz_result = await asyncio.wait_for(
                    self._process_single_quiz(current_url, email, secret),
                    timeout=30.0  # 30 second timeout per quiz
                )
            except asyncio.TimeoutError:
                quiz_result = {
                    'url': current_url,
                    'success': False,
                    'error': 'Processing timeout (30s)',
                    'correct': False,
                    'next_url': None
                }
            
            results['chain'].append(quiz_result)
            
            if quiz_result.get('correct'):
                results['correct_answers'] += 1
            
            # Get next URL
            current_url = quiz_result.get('next_url')
            
            if not current_url:
                results['completed'] = True
                logger.info("Quiz chain completed - no more URLs")
                break
                
            # Minimal delay between quizzes
            await asyncio.sleep(0.5)  # Reduced from 1 second
        
        if attempt >= self.max_attempts:
            logger.warning(f"Reached maximum attempts ({self.max_attempts})")
        
        return results
    
    async def _process_single_quiz(self, url: str, email: str, secret: str) -> Dict[str, Any]:
        """
        Process a single quiz question
        """
        result = {
            'url': url,
            'success': False,
            'error': None,
            'instructions': None,
            'answer': None,
            'correct': False,
            'next_url': None
        }
        
        try:
            # Step 1: Scrape the page
            html_content, error = await scraper.scrape_page(url)
            if error:
                result['error'] = f"Scraping failed: {error}"
                return result
            
            # Step 2: Parse instructions
            instructions = quiz_parser.parse_quiz_instructions(html_content)
            result['instructions'] = instructions
            
            # Step 3: Process task and generate answer (pass base_url for relative URLs)
            processing_result = await data_processor.process_quiz_task(instructions, base_url=url)
            result['answer'] = processing_result.get('answer')
            
            # Step 4: Submit answer if we have one and a submit URL
            submit_url = instructions.get('submit_url')
            if result['answer'] is not None and submit_url is not None:
                # Handle relative submit URLs
                if submit_url.startswith('/'):
                    from urllib.parse import urljoin
                    submit_url = urljoin(url, submit_url)
                
                submission_result = await answer_submitter.submit_answer(
                    submit_url=submit_url,
                    email=email,
                    secret=secret,
                    quiz_url=url,
                    answer=result['answer']
                )
                
                result['correct'] = submission_result.get('correct', False)
                result['next_url'] = submission_result.get('next_url')
                result['submission_result'] = submission_result
                result['success'] = True
                
                logger.info(f"Quiz submitted - Correct: {result['correct']}, Next URL: {result['next_url']}")
            else:
                result['error'] = "No answer generated or no submit URL found"
                result['success'] = False
        
        except Exception as e:
            result['error'] = f"Processing error: {str(e)}"
            logger.error(f"Error processing quiz {url}: {str(e)}")
        
        return result

# Global solver instance
quiz_solver = QuizSolver()