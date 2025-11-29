with open('web_scraper.py', 'r') as f:
    content = f.read()

# Make JS detection more aggressive
new_content = content.replace(
    'if self._definitely_needs_js(html_content):',
    'if self._definitely_needs_js(html_content) or "document.querySelector" in html_content or "innerHTML" in html_content or "atob(" in html_content:'
)

with open('web_scraper.py', 'w') as f:
    f.write(new_content)

print("Fixed JS detection to be more aggressive")
