import re
import base64
from bs4 import BeautifulSoup
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class QuizParser:
    def __init__(self):
        self.soup = None
    
    def parse_quiz_instructions(self, html_content: str) -> Dict[str, Any]:
        """
        Extract quiz instructions from HTML content
        Returns structured information about the quiz task
        """
        self.soup = BeautifulSoup(html_content, 'html.parser')
        
        instructions = {
            'question': None,
            'data_source': None,
            'task_type': None,
            'submit_url': None,
            'answer_format': None,
            'extracted_content': None,
            'secret_code_pattern': None
        }
        
        # Extract visible text content
        visible_text = self._extract_visible_text()
        instructions['extracted_content'] = visible_text
        
        # Parse question
        instructions['question'] = self._extract_question(visible_text)
        
        # Parse data source
        instructions['data_source'] = self._extract_data_source()
        
        # Parse submit URL
        instructions['submit_url'] = self._extract_submit_url()
        
        # Determine task type
        instructions['task_type'] = self._determine_task_type(visible_text)
        
        # Determine answer format
        instructions['answer_format'] = self._determine_answer_format(visible_text)
        
        # Extract secret code pattern if mentioned
        instructions['secret_code_pattern'] = self._extract_secret_code_pattern(visible_text)
        
        logger.info(f"Parsed quiz instructions: {instructions}")
        return instructions
    
    def _extract_visible_text(self) -> str:
        """Extract all visible text from the page"""
        # Remove script and style elements
        for script in self.soup(["script", "style"]):
            script.decompose()
        
        # Get text and clean it
        text = self.soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _extract_question(self, text: str) -> Optional[str]:
        """Extract the main question from text"""
        # Look for patterns like "Q834." or "What is..."
        patterns = [
            r'Q\d+\.\s*(.+)',
            r'([Ss]crape\s+.+?)(?:\.|POST|$)',
            r'([Gg]et\s+.+?)(?:\.|POST|$)',
            r'([Cc]alculate\s+.+?)(?:\.|POST|$)',
            r'([Ff]ind\s+.+?)(?:\.|POST|$)',
            r'^(.{20,100}?)(?:\.|POST|$)'  # First meaningful phrase
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                question = match.group(1).strip()
                # Clean up the question
                if question.endswith('POST') or question.endswith('Post'):
                    question = question[:-4].strip()
                return question
        
        return None
    
    def _extract_data_source(self) -> Optional[str]:
        """Extract data source URLs or file references"""
        # Look for download links
        download_links = self.soup.find_all('a', href=True)
        for link in download_links:
            href = link.get('href', '')
            if any(ext in href.lower() for ext in ['.pdf', '.csv', '.xlsx', '.json', '.txt']):
                return href
        
        # Look for API endpoints
        if 'api' in self.soup.get_text().lower():
            api_pattern = r'https?://[^\s]+api[^\s]+'
            match = re.search(api_pattern, self.soup.get_text())
            if match:
                return match.group()
        
        # Look for relative URLs mentioned in text
        text = self.soup.get_text()
        relative_patterns = [
            r'[Ss]crape\s+([^\s]+)',
            r'[Vv]isit\s+([^\s]+)',
            r'[Gg]o\s+to\s+([^\s]+)',
            r'/(?:[\w-]+\.)+(?:csv|pdf|json|txt)\??\S*',
            r'/([\w/-]+)\??\S*'
        ]
        
        for pattern in relative_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                if match.startswith('/') or any(ext in match.lower() for ext in ['.csv', '.pdf', '.json', '.txt']):
                    return match
        
        return None
    
    def _extract_submit_url(self) -> Optional[str]:
        """Extract the submission endpoint URL"""
        # Look for submit URLs in text
        text = self.soup.get_text()
        
        # More specific patterns for the demo page
        submit_patterns = [
            r'POST\s+this\s+JSON\s+to\s+(https?://[^\s/]+/submit)',
            r'POST\s+this\s+JSON\s+to\s+(/submit)',
            r'[Ss]ubmit\s+to\s+(https?://[^\s/]+/submit)',
            r'[Ss]ubmit\s+to\s+(/submit)',
            r'https?://[^\s/]+/submit',
            r'/submit'
        ]
        
        for pattern in submit_patterns:
            matches = re.findall(pattern, text)
            if matches:
                submit_url = matches[0]
                # Ensure it's a full URL
                if submit_url.startswith('http'):
                    return submit_url
                elif submit_url.startswith('/'):
                    return submit_url
        
        return None
    
    def _extract_secret_code_pattern(self, text: str) -> Optional[str]:
        """Extract patterns that might indicate secret codes"""
        patterns = [
            r'[Ss]ecret\s+[Cc]ode[:\s]*([^\s]+)',
            r'[Cc]ode[:\s]*([^\s]{4,})',
            r'[Kk]ey[:\s]*([^\s]{4,})',
            r'[Pp]assword[:\s]*([^\s]{4,})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def _determine_task_type(self, text: str) -> str:
        """Determine the type of task"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['sum', 'total', 'calculate', 'count']):
            return 'calculation'
        elif any(word in text_lower for word in ['download', 'file', 'pdf', 'csv']):
            return 'data_extraction'
        elif any(word in text_lower for word in ['filter', 'sort', 'find']):
            return 'data_processing'
        elif any(word in text_lower for word in ['chart', 'graph', 'visualize']):
            return 'visualization'
        elif any(word in text_lower for word in ['api', 'endpoint']):
            return 'api_call'
        elif any(word in text_lower for word in ['scrape', 'extract', 'get secret']):
            return 'scraping'
        else:
            return 'general'
    
    def _determine_answer_format(self, text: str) -> str:
        """Determine the expected answer format"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['number', 'sum', 'total', 'count']):
            return 'number'
        elif any(word in text_lower for word in ['string', 'text', 'code']):
            return 'string'
        elif any(word in text_lower for word in ['true', 'false', 'boolean']):
            return 'boolean'
        elif any(word in text_lower for word in ['json', 'object']):
            return 'json'
        elif any(word in text_lower for word in ['base64', 'file', 'attachment']):
            return 'base64'
        else:
            return 'unknown'

# Global parser instance
quiz_parser = QuizParser()