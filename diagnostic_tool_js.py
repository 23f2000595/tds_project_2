
#!/usr/bin/env python3
"""
Enhanced diagnostic tool with JavaScript rendering support
"""

import httpx
import logging
from bs4 import BeautifulSoup
import re
from typing import Dict, Any, Optional, List
import csv
import io
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

logger = logging.getLogger(__name__)

class EnhancedDiagnosticTool:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def diagnose_quiz_problem(self, url: str, email: str, secret: str) -> Dict[str, Any]:
        """
        Comprehensive diagnosis of quiz problems with JS support
        """
        diagnosis = {
            'url': url,
            'steps': [],
            'issues': [],
            'recommendations': []
        }
        
        # Step 1: Scrape the page with JavaScript rendering
        scrape_result = await self._diagnose_scraping_with_js(url)
        diagnosis['steps'].append(scrape_result)
        
        if not scrape_result['success']:
            diagnosis['issues'].append("Failed to scrape the page")
            return diagnosis
        
        html_content = scrape_result['content']
        
        # Step 2: Parse instructions from rendered content
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
    
    async def _diagnose_scraping_with_js(self, url: str) -> Dict[str, Any]:
        """Diagnose scraping issues with JavaScript rendering"""
        result = {
            'step': 'scraping_with_js',
            'success': False,
            'details': {}
        }
        
        driver = None
        try:
            # First try without JS
            response = await self.client.get(url)
            result['details']['direct_status'] = response.status_code
            result['details']['direct_content_length'] = len(response.text)
            
            # Check if JS is needed
            soup = BeautifulSoup(response.text, 'html.parser')
            scripts = soup.find_all('script')
            has_js_content = any('document' in str(script) for script in scripts)
            
            result['details']['needs_js'] = has_js_content
            result['details']['script_count'] = len(scripts)
            
            if has_js_content:
                # Use Selenium for JS rendering
                chrome_options = Options()
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                
                driver = webdriver.Chrome(options=chrome_options)
                driver.get(url)
                await asyncio.sleep(3)  # Wait for JS to execute
                
                rendered_html = driver.page_source
                result['content'] = rendered_html
                result['success'] = True
                
                # Analyze rendered content
                rendered_soup = BeautifulSoup(rendered_html, 'html.parser')
                for script in rendered_soup(["script", "style"]):
                    script.decompose()
                rendered_text = rendered_soup.get_text()
                result['details']['rendered_text'] = rendered_text[:1000] + "..." if len(rendered_text) > 1000 else rendered_text
                result['details']['rendered_content_length'] = len(rendered_html)
                
            else:
                # No JS needed, use direct content
                result['content'] = response.text
                result['success'] = True
                result['details']['direct_text'] = soup.get_text()[:1000] + "..." if len(soup.get_text()) > 1000 else soup.get_text()
                
        except Exception as e:
            result['details']['error'] = str(e)
        finally:
            if driver:
                driver.quit()
        
        return result
    
    async def _diagnose_parsing(self, html_content: str, base_url: str) -> Dict[str, Any]:
        """Diagnose instruction parsing from rendered content"""
        result = {
            'step': 'parsing',
            'success': False,
            'instructions': {},
            'details': {}
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text()
            
            # Clean and extract text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = ' '.join(chunk for chunk in chunks if chunk)
            
            result['details']['raw_text'] = clean_text[:1000]
            
            # Parse question from rendered content
            question = None
            if clean_text.strip():
                # More flexible patterns for rendered content
                question_patterns = [
                    r'Scrape\s+(.+?)(?:\.|POST|$)',
                    r'Get\s+(.+?)(?:\.|POST|$)',
                    r'Visit\s+(.+?)(?:\.|POST|$)',
                    r'([^.!?]*(?:scrape|get|visit|find)[^.!?]*[.!?])',
                    r'^([^.!?]{20,200}?[.!?])'  # First meaningful sentence
                ]
                
                for pattern in question_patterns:
                    match = re.search(pattern, clean_text, re.IGNORECASE)
                    if match:
                        question = match.group(1).strip()
                        break
            
            # Parse data source - look for URLs and paths
            data_source = None
            source_patterns = [
                r'Scrape\s+([^\s.!?]+)',
                r'Visit\s+([^\s.!?]+)',
                r'Go to\s+([^\s.!?]+)',
                r'/(?:[\w-]+\.)+(?:csv|pdf|json|txt)\??\S*',
                r'/([\w/-]+)\??\S*'
            ]
            
            for pattern in source_patterns:
                matches = re.findall(pattern, clean_text, re.IGNORECASE)
                for match in matches:
                    if match.startswith('/') or any(ext in match.lower() for ext in ['.csv', '.pdf', '.json', '.txt']):
                        data_source = match
                        break
            
            # Parse submit URL
            submit_url = None
            submit_patterns = [
                r'POST\s+.*?\s+to\s+(https?://[^\s/]+/submit)',
                r'POST\s+.*?\s+to\s+(/submit)',
                r'Submit\s+to\s+(https?://[^\s/]+/submit)',
                r'Submit\s+to\s+(/submit)',
                r'https?://[^\s/]+/submit',
                r'/submit'
            ]
            
            for pattern in submit_patterns:
                matches = re.findall(pattern, clean_text, re.IGNORECASE)
                if matches:
                    submit_url = matches[0]
                    break
            
            # Determine answer format
            answer_format = 'unknown'
            text_lower = clean_text.lower()
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
                'raw_text_preview': clean_text[:500]
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
        
        # Analyze what type of answer is needed
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
        scraping_step = next((s for s in diagnosis['steps'] if s['step'] == 'scraping_with_js'), None)
        if scraping_step:
            if not scraping_step['success']:
                recommendations.append("Fix scraping: The page cannot be accessed")
            elif scraping_step['details'].get('needs_js'):
                recommendations.append("Page requires JavaScript rendering - using Selenium")
        
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
enhanced_diagnostic_tool = EnhancedDiagnosticTool()

async def main():
    import sys
    
    if len(sys.argv) != 4:
        print("Usage: python diagnostic_tool_js.py <email> <secret> <url>")
        print("Example: python diagnostic_tool_js.py test@example.com mysecret https://example.com/quiz-123")
        return
    
    email = sys.argv[1]
    secret = sys.argv[2]
    url = sys.argv[3]
    
    print(f"🔍 Diagnosing quiz (with JS support): {url}")
    print("=" * 60)
    
    diagnosis = await enhanced_diagnostic_tool.diagnose_quiz_problem(url, email, secret)
    
    # Print formatted results
    print(f"📋 URL: {diagnosis['url']}")
    print()
    
    # Print steps
    for step in diagnosis['steps']:
        print(f"🔧 {step['step'].upper()}: {'✅ SUCCESS' if step['success'] else '❌ FAILED'}")
        
        if not step['success']:
            print(f"   Error: {step['details'].get('error', 'Unknown error')}")
        else:
            # Print relevant details for each step
            if step['step'] == 'scraping_with_js':
                print(f"   Direct Status: {step['details'].get('direct_status')}")
                print(f"   Needs JS: {step['details'].get('needs_js', False)}")
                if step['details'].get('needs_js'):
                    print(f"   Rendered Text: {step['details'].get('rendered_text', '')[:200]}...")
                else:
                    print(f"   Direct Text: {step['details'].get('direct_text', '')[:200]}...")
                
            elif step['step'] == 'parsing':
                instructions = step['instructions']
                print(f"   Question: {instructions.get('question', 'Not found')}")
                print(f"   Data Source: {instructions.get('data_source', 'Not found')}")
                print(f"   Submit URL: {instructions.get('submit_url', 'Not found')}")
                print(f"   Answer Format: {instructions.get('answer_format', 'Not found')}")
                
            elif step['step'] == 'data_source_analysis':
                print(f"   Resolved URL: {step['details'].get('resolved_url')}")
                print(f"   Status: {step['details'].get('status_code')}")
                secrets = step['details'].get('potential_secrets', [])
                if secrets:
                    print(f"   🔑 Potential Secrets Found: {secrets}")
                else:
                    print(f"   ❌ No secrets found in content")
                print(f"   Content Preview: {step['details'].get('content_preview', '')[:200]}...")
                
            elif step['step'] == 'question_analysis':
                print(f"   Answer Type: {step['details'].get('answer_type')}")
                print(f"   Expected Action: {step['details'].get('expected_action')}")
                
            elif step['step'] == 'submission_test':
                print(f"   Submission Status: {step['details'].get('submission_status')}")
                print(f"   Correct: {step['details'].get('correct')}")
                print(f"   Reason: {step['details'].get('reason')}")
                if step['details'].get('next_url'):
                    print(f"   Next URL: {step['details'].get('next_url')}")
        
        print()
    
    # Print recommendations
    if diagnosis['recommendations']:
        print("💡 RECOMMENDATIONS:")
        for rec in diagnosis['recommendations']:
            print(f"   • {rec}")
    else:
        print("✅ No major issues detected")
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())