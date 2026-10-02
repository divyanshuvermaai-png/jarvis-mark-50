"""
Browser Agent — Page Reader & Summarizer
Fetches any webpage, strips HTML, and returns clean text.
Uses only built-in Python libraries.
"""
import urllib.request
import urllib.parse
import re
import html


class PageReader:
    """Read and extract content from any webpage."""
    
    USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    @staticmethod
    def read_page(url, max_chars=5000):
        """
        Fetch a webpage and extract its main text content.
        Returns: {'success': bool, 'title': str, 'text': str, 'url': str}
        """
        try:
            # Ensure URL has a scheme
            if not url.startswith('http'):
                url = 'https://' + url
            
            req = urllib.request.Request(url, headers={
                'User-Agent': PageReader.USER_AGENT,
                'Accept': 'text/html,application/xhtml+xml',
                'Accept-Language': 'en-US,en;q=0.9',
            })
            
            with urllib.request.urlopen(req, timeout=15) as resp:
                content_type = resp.headers.get('Content-Type', '')
                if 'text/html' not in content_type and 'application/xhtml' not in content_type:
                    return {
                        'success': False,
                        'title': '',
                        'text': f'URL returned non-HTML content: {content_type}',
                        'url': url
                    }
                
                raw_html = resp.read().decode('utf-8', errors='ignore')
            
            # Extract title
            title_match = re.search(r'<title[^>]*>(.*?)</title>', raw_html, re.IGNORECASE | re.DOTALL)
            title = html.unescape(title_match.group(1).strip()) if title_match else 'Untitled'
            
            # Extract main content
            text = PageReader._extract_text(raw_html, max_chars)
            
            return {
                'success': True,
                'title': title,
                'text': text,
                'url': url
            }
            
        except Exception as e:
            return {
                'success': False,
                'title': '',
                'text': f'Failed to read page: {str(e)}',
                'url': url
            }
    
    @staticmethod
    def _extract_text(raw_html, max_chars=5000):
        """Extract clean text from HTML, prioritizing article/main content."""
        
        # Try to find the main content area
        main_content = None
        for tag in ['article', 'main', 'div[^>]+role="main"', 'div[^>]+class="[^"]*content[^"]*"']:
            pattern = re.compile(
                f'<{tag}[^>]*>(.*?)</{tag.split("[")[0]}>',
                re.IGNORECASE | re.DOTALL
            )
            match = pattern.search(raw_html)
            if match:
                main_content = match.group(1)
                break
        
        if not main_content:
            # Fall back to body
            body_match = re.search(r'<body[^>]*>(.*?)</body>', raw_html, re.IGNORECASE | re.DOTALL)
            main_content = body_match.group(1) if body_match else raw_html
        
        # Remove unwanted elements
        for tag in ['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript', 'svg']:
            main_content = re.sub(
                f'<{tag}[^>]*>.*?</{tag}>', '', main_content,
                flags=re.IGNORECASE | re.DOTALL
            )
        
        # Remove HTML comments
        main_content = re.sub(r'<!--.*?-->', '', main_content, flags=re.DOTALL)
        
        # Convert <br>, <p>, <div>, <li> to newlines
        main_content = re.sub(r'<br\s*/?>', '\n', main_content, flags=re.IGNORECASE)
        main_content = re.sub(r'</?(p|div|li|h[1-6]|tr|blockquote)[^>]*>', '\n', main_content, flags=re.IGNORECASE)
        
        # Remove all remaining HTML tags
        text = re.sub(r'<[^>]+>', '', main_content)
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Clean up whitespace
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if line and len(line) > 2:  # Skip very short lines (likely artifacts)
                lines.append(line)
        
        text = '\n'.join(lines)
        
        # Trim to max length
        if len(text) > max_chars:
            text = text[:max_chars] + '\n\n[Content truncated...]'
        
        return text if text.strip() else 'Could not extract readable text from this page.'
    
    @staticmethod
    def extract_links(url, max_links=20):
        """Extract all links from a webpage."""
        try:
            if not url.startswith('http'):
                url = 'https://' + url
            
            req = urllib.request.Request(url, headers={
                'User-Agent': PageReader.USER_AGENT,
            })
            
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw_html = resp.read().decode('utf-8', errors='ignore')
            
            # Find all <a> tags with href
            link_pattern = re.compile(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
            matches = link_pattern.findall(raw_html)
            
            links = []
            seen = set()
            for href, text in matches:
                text = re.sub(r'<[^>]+>', '', text).strip()
                if not text or len(text) < 2:
                    continue
                
                # Resolve relative URLs
                if href.startswith('/'):
                    parsed = urllib.parse.urlparse(url)
                    href = f"{parsed.scheme}://{parsed.netloc}{href}"
                elif not href.startswith('http'):
                    continue
                
                if href not in seen:
                    seen.add(href)
                    links.append({'text': text[:100], 'url': href})
                
                if len(links) >= max_links:
                    break
            
            return {'success': True, 'links': links}
            
        except Exception as e:
            return {'success': False, 'links': [], 'error': str(e)}
