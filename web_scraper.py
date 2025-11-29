import httpx
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin
import asyncio
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)  # Reduced timeout
    
    async def scrape_page(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        try:
            # Try direct request first (fastest)
            response = await self.client.get(url)
            response.raise_for_status()
            
            html_content = response.text
            
            # Only use Selenium if absolutely necessary
            if self._definitely_needs_js(html_content):
                logger.info("Page definitely needs JavaScript rendering")
                return await self._scrape_with_selenium_fast(url)
            else:
                logger.info("Static page scraped successfully (fast)")
                return html_content, None
                
        except Exception as e:
            error_msg = f"Error scraping {url}: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    def _definitely_needs_js(self, html: str) -> bool:
        """Only use Selenium if we're sure JS is needed"""
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text().strip()
        
        # If there's meaningful content without JS, don't use Selenium
        if len(text) > 50 and any(keyword in text.lower() for keyword in ['scrape', 'secret', 'code', 'submit']):
            return False
            
        # Only use Selenium for completely empty pages or specific JS patterns
        scripts = soup.find_all('script')
        has_complex_js = any('document.querySelector' in str(script) for script in scripts)
        
        return len(text) < 20 and has_complex_js
    
    async def _scrape_with_selenium_fast(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Ultra-fast Selenium with minimal delays"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-proxy-server")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = None
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(5)  # Very short timeout
            driver.implicitly_wait(1)  # Short implicit wait
            driver.get(url)
            await asyncio.sleep(1)  # Minimal wait for JS
            html_content = driver.page_source
            return html_content, None
            
        except Exception as e:
            logger.warning(f"Fast Selenium failed, falling back to direct content: {str(e)}")
            # Fallback to direct request
            try:
                response = await self.client.get(url)
                return response.text, None
            except:
                return None, f"All scraping methods failed: {str(e)}"
        finally:
            if driver:
                driver.quit()
    
    async def close(self):
        await self.client.aclose()

scraper = WebScraper()