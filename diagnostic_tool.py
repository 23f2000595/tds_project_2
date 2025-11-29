import httpx
import logging
from bs4 import BeautifulSoup
import re
from typing import Dict, Any, Optional, List
import csv
import io

logger = logging.getLogger(__name__)

class DiagnosticTool:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def diagnose_quiz_problem(self, url: str, email: str, secret: str) -> Dict[str, Any]:
        """
        Comprehensive diagnosis of quiz problems
        """
        diagnosis = {
            'url': url,
            'steps': [],
            'issues': [],
            'recommendations': []
        }
        
        # Step 1: Scrape the page
        scrape_result = await self._diagnose_scraping(url)
        diagnosis['steps'].append(scrape_result)
        
        if not scrape_result['success']:
            diagnosis['issues'].append("Failed to scrape the page")
            return diagnosis
        
        html_content = scrape_result['content']
        
        # Step 2: Parse instructions
        parse_result = await self._diagnose_parsing(html_content, url)
        diagnosis['steps'].append(parse_result)
        
        instructions = parse_result['instructions']
        
        # Step 3: Analyze data source
        if instructions.get('data_source'):
            data_source_result = await self._diagnose_data_source(instructions['data_source'], url)
            diagnosis['steps'].append(data_source_result)
        
        # Step 4: Analyze question and expected answer
        question_result = self._diagnose_question(instructions)
        diagnosis['steps'].append(question_result)
        
        # Step 5: Generate test submission
        if instructions.get('submit_url'):
            submission_result = await self._diagnose_submission(instructions, url, email, secret)
            diagnosis['steps'].append(submission_result)
        
        # Generate overall recommendations
        diagnosis['recommendations'] = self._generate_recommendations(diagnosis)
        
        return diagnosis
    
    async def _diagnose_scraping(self, url: str) -> Dict[str, Any]:
        """Diagnose scraping issues"""
        result = {
            'step': 'scraping',
            'success': False,
            'details': {}
        }
        
        try:
            response = await self.client.get(url)
            result['details']['status_code'] = response.status_code
            result['details']['content_type'] = response.headers.get('content-type')
            result['details']['content_length'] = len(response.text)
            
            if response.status_code == 200:
                result['success'] = True
                result['content'] = response.text
                
                # Check for JavaScript content
                soup = BeautifulSoup(response.text, 'html.parser')
                scripts = soup.find_all('script')
                result['details']['script_count'] = len(scripts)
                result['details']['has_js_content'] = any('document' in str(script) for script in scripts)
                
                # Extract visible text preview
                for script in soup(["script", "style"]):
                    script.decompose()
                text = soup.get_text()
                result['details']['visible_text'] = text[:500] + "..." if len(text) > 500 else text
            else:
                result['details']['error'] = f"HTTP {response.status_code}"
                
        except Exception as e:
            result['details']['error'] = str(e)
        
        return result
    
    async def _diagnose_parsing(self, html_content: str, base_url: str) -> Dict[str, Any]:
        """Diagnose instruction parsing"""
        result = {
            'step': 'parsing',
            'success': False,
            'instructions': {},
            'details': {}
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text()
            
            # Extract key elements
            result['details']['raw_text'] = text[:1000]
            
            # Parse question - handle None case
            question = None
            if text.strip():
                question_patterns = [
                    r'Q\d+\.\s*(.+)',
                    r'([Ss]crape\s+.+?[.!])',
                    r'([Gg]et\s+.+?[.!])',
                    r'([Cc]alculate\s+.+?[.!])',
                    r'([Ff]ind\s+.+?[.!])',
                    r'^(.{20,100}?[.!])'  # First sentence as fallback
                ]
                
                for pattern in question_patterns:
                    match = re.search(pattern, text)
                    if match:
                        question = match.group(1).strip()
                        break
            
            # Parse data source
            data_source = None
            source_patterns = [
                r'[Ss]crape\s+([^\s]+)',
                r'[Vv]isit\s+([^\s]+)',
                r'[Gg]o\s+to\s+([^\s]+)',
                r'([/\w-]+\.(csv|pdf|json|txt))'
            ]
            
            for pattern in source_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]
                    if match.startswith('/') or any(ext in match for ext in ['.csv', '.pdf', '.json']):
                        data_source = match
                        break
            
            # Parse submit URL
            submit_url = None
            submit_patterns = [
                r'[Pp]OST\s+.*?\s+to\s+(https?://[^\s/]+/submit)',
                r'[Pp]OST\s+.*?\s+to\s+(/submit)',
                r'[Ss]ubmit\s+to\s+(https?://[^\s/]+/submit)',
                r'[Ss]ubmit\s+to\s+(/submit)'
            ]
            
            for pattern in submit_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    submit_url = matches[0]
                    break
            
            # Determine answer format
            answer_format = 'unknown'
            text_lower = text.lower()
            if any(word in text_lower for word in ['number', 'sum', 'total', 'count']):
                answer_format = 'number'
            elif any(word in text_lower for word in ['string', 'text', 'code']):
                answer_format = 'string'
            elif any(word in text_lower for word in ['json', 'object']):
                answer_format = 'json'
            
            result['instructions'] = {
                'question': question,
                'data_source': data_source,
                'submit_url': submit_url,
                'answer_format': answer_format,
                'raw_text_preview': text[:500]
            }
            result['success'] = True
            
        except Exception as e:
            result['details']['error'] = str(e)
        
        return result
    
    async def _diagnose_data_source(self, data_source: str, base_url: str) -> Dict[str, Any]:
        """Diagnose data source accessibility and content"""
        result = {
            'step': 'data_source_analysis',
            'success': False,
            'details': {}
        }
        
        try:
            # Handle relative URLs
            if data_source.startswith('/'):
                from urllib.parse import urljoin
                data_source = urljoin(base_url, data_source)
            
            result['details']['resolved_url'] = data_source
            
            response = await self.client.get(data_source)
            result['details']['status_code'] = response.status_code
            result['details']['content_type'] = response.headers.get('content-type')
            result['details']['content_length'] = len(response.text)
            
            if response.status_code == 200:
                result['success'] = True
                
                # Analyze content
                content = response.text
                result['details']['content_preview'] = content[:1000] + "..." if len(content) > 1000 else content
                
                # Check for secret codes
                secret_patterns = [
                    r'[Ss]ecret[:\s]*([A-Za-z0-9]{6,})',
                    r'[Cc]ode[:\s]*([A-Za-z0-9]{6,})',
                    r'[Kk]ey[:\s]*([A-Za-z0-9]{6,})',
                    r'([A-Z0-9]{8,})',
                    r'([a-zA-Z0-9]{10,})'
                ]
                
                found_secrets = []
                for pattern in secret_patterns:
                    matches = re.findall(pattern, content)
                    found_secrets.extend(matches)
                
                result['details']['potential_secrets'] = found_secrets
                
                # For CSV files
                if data_source.endswith('.csv'):
                    csv_reader = csv.reader(io.StringIO(content))
                    rows = list(csv_reader)
                    result['details']['csv_row_count'] = len(rows)
                    result['details']['csv_columns'] = rows[0] if rows else []
                    result['details']['csv_preview'] = rows[:5] if len(rows) > 5 else rows
                    
            else:
                result['details']['error'] = f"Failed to fetch data source: HTTP {response.status_code}"
                
        except Exception as e:
            result['details']['error'] = str(e)
        
        return result
    
    def _diagnose_question(self, instructions: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the question and expected answer format"""
        result = {
            'step': 'question_analysis',
            'success': True,
            'details': {}
        }
        
        question = instructions.get('question', '')
        data_source = instructions.get('data_source', '')
        answer_format = instructions.get('answer_format', '')
        
        result['details']['question'] = question
        result['details']['data_source'] = data_source
        result['details']['expected_answer_format'] = answer_format
        
        # Analyze what type of answer is needed - handle None question
        question_lower = (question or '').lower()
        if 'scrape' in question_lower and 'secret' in question_lower:
            result['details']['answer_type'] = 'secret_code_extraction'
            result['details']['expected_action'] = 'Extract a secret code from the data source'
        elif 'scrape' in question_lower:
            result['details']['answer_type'] = 'content_extraction'
            result['details']['expected_action'] = 'Extract specific content from the data source'
        elif data_source and data_source.endswith('.csv'):
            result['details']['answer_type'] = 'csv_processing'
            result['details']['expected_action'] = 'Process CSV data and extract specific information'
        elif 'calculate' in question_lower:
            result['details']['answer_type'] = 'calculation'
            result['details']['expected_action'] = 'Perform a calculation on the data'
        else:
            result['details']['answer_type'] = 'unknown'
            result['details']['expected_action'] = 'Unknown - needs manual analysis'
        
        return result
    
    async def _diagnose_submission(self, instructions: Dict[str, Any], quiz_url: str, email: str, secret: str) -> Dict[str, Any]:
        """Test submission with a sample answer"""
        result = {
            'step': 'submission_test',
            'success': False,
            'details': {}
        }
        
        try:
            submit_url = instructions['submit_url']
            
            # Handle relative submit URLs
            if submit_url.startswith('/'):
                from urllib.parse import urljoin
                submit_url = urljoin(quiz_url, submit_url)
            
            result['details']['resolved_submit_url'] = submit_url
            
            # Create a test payload
            test_payload = {
                "email": email,
                "secret": secret,
                "url": quiz_url,
                "answer": "test_diagnostic_answer"
            }
            
            response = await self.client.post(
                submit_url,
                json=test_payload,
                headers={"Content-Type": "application/json"}
            )
            
            result['details']['submission_status'] = response.status_code
            result['details']['submission_response'] = response.json() if response.status_code == 200 else response.text
            
            if response.status_code == 200:
                result['success'] = True
                submission_data = response.json()
                result['details']['correct'] = submission_data.get('correct', False)
                result['details']['reason'] = submission_data.get('reason', '')
                result['details']['next_url'] = submission_data.get('url', '')
                
        except Exception as e:
            result['details']['error'] = str(e)
        
        return result
    
    def _generate_recommendations(self, diagnosis: Dict[str, Any]) -> List[str]:
        """Generate specific recommendations based on diagnosis"""
        recommendations = []
        
        # Check scraping issues
        scraping_step = next((s for s in diagnosis['steps'] if s['step'] == 'scraping'), None)
        if scraping_step and not scraping_step['success']:
            recommendations.append("Fix scraping: The page cannot be accessed")
        
        # Check parsing issues
        parsing_step = next((s for s in diagnosis['steps'] if s['step'] == 'parsing'), None)
        if parsing_step and parsing_step['success']:
            instructions = parsing_step['instructions']
            if not instructions.get('question'):
                recommendations.append("Improve question parsing: Could not identify the main question")
            if not instructions.get('data_source') and 'scrape' in (instructions.get('question') or '').lower():
                recommendations.append("Fix data source detection: Could not find the URL to scrape")
        
        # Check data source issues
        data_source_step = next((s for s in diagnosis['steps'] if s['step'] == 'data_source_analysis'), None)
        if data_source_step:
            if not data_source_step['success']:
                recommendations.append(f"Fix data source access: {data_source_step['details'].get('error', 'Unknown error')}")
            elif data_source_step['details'].get('potential_secrets'):
                recommendations.append(f"Found potential secrets: {data_source_step['details']['potential_secrets']}")
        
        # Check submission issues
        submission_step = next((s for s in diagnosis['steps'] if s['step'] == 'submission_test'), None)
        if submission_step and submission_step['success']:
            if not submission_step['details'].get('correct', False):
                reason = submission_step['details'].get('reason', '')
                recommendations.append(f"Submission rejected: {reason}")
        
        return recommendations

# Global diagnostic instance
diagnostic_tool = DiagnosticTool()