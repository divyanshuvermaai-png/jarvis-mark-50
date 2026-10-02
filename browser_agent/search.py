"""
Browser Agent — Web Search & Result Extraction
Uses urllib (built-in) with no external dependencies.
Falls back to opening browser if extraction fails.
"""
import urllib.request
import urllib.parse
import re
import json
import os
import subprocess


class WebSearchAgent:
    """Search the web and extract results without opening a browser."""
    
    USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    @staticmethod
    def search(query, num_results=5):
        """
        Search Google and return structured results.
        Returns: {'success': bool, 'results': [{'title', 'url', 'snippet'}], 'summary': str}
        """
        try:
            # Try DuckDuckGo Lite (simpler HTML, easier to parse)
            results = WebSearchAgent._search_ddg(query, num_results)
            if results:
                summary = WebSearchAgent._format_summary(query, results)
                return {'success': True, 'results': results, 'summary': summary}
        except Exception as e:
            print(f"  [BrowserAgent] DDG search error: {e}")
        
        # Fallback: open in default browser
        try:
            encoded = urllib.parse.quote_plus(query)
            subprocess.Popen(['open', f'https://www.google.com/search?q={encoded}'])
            return {
                'success': True, 
                'results': [],
                'summary': f"I've opened a Google search for '{query}' in your browser, sir."
            }
        except Exception as e:
            return {'success': False, 'results': [], 'summary': f"Search failed: {e}"}
    
    @staticmethod
    def _search_ddg(query, num_results=5):
        """Search DuckDuckGo Lite and parse results."""
        encoded = urllib.parse.quote_plus(query)
        url = f"https://lite.duckduckgo.com/lite/?q={encoded}"
        
        req = urllib.request.Request(url, headers={
            'User-Agent': WebSearchAgent.USER_AGENT,
            'Accept': 'text/html',
        })
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        
        results = []
        
        # Parse DuckDuckGo Lite results
        # Results are in <a> tags with class="result-link"
        link_pattern = re.compile(
            r'<a[^>]+rel="nofollow"[^>]+href="([^"]+)"[^>]*>(.+?)</a>',
            re.IGNORECASE | re.DOTALL
        )
        snippet_pattern = re.compile(
            r'<td[^>]*class="result-snippet"[^>]*>(.*?)</td>',
            re.IGNORECASE | re.DOTALL
        )
        
        links = link_pattern.findall(html)
        snippets = snippet_pattern.findall(html)
        
        for i, (href, title) in enumerate(links[:num_results]):
            title_clean = re.sub(r'<[^>]+>', '', title).strip()
            snippet = ''
            if i < len(snippets):
                snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip()
            
            # Skip DuckDuckGo internal links
            if 'duckduckgo.com' in href:
                continue
                
            results.append({
                'title': title_clean,
                'url': href,
                'snippet': snippet
            })
        
        return results[:num_results]
    
    @staticmethod
    def _format_summary(query, results):
        """Format search results into a readable summary."""
        if not results:
            return f"No results found for '{query}'."
        
        summary = f"Here's what I found for '{query}', sir:\n\n"
        for i, r in enumerate(results, 1):
            summary += f"{i}. **{r['title']}**\n"
            if r['snippet']:
                summary += f"   {r['snippet']}\n"
            summary += f"   🔗 {r['url']}\n\n"
        
        return summary.strip()
    
    @staticmethod
    def quick_answer(query):
        """
        Try to get an instant answer from DuckDuckGo API.
        Good for: definitions, calculations, quick facts.
        """
        try:
            encoded = urllib.parse.quote_plus(query)
            url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1"
            
            req = urllib.request.Request(url, headers={
                'User-Agent': WebSearchAgent.USER_AGENT
            })
            
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            
            # Try AbstractText (definition/summary)
            if data.get('AbstractText'):
                return {
                    'success': True,
                    'answer': data['AbstractText'],
                    'source': data.get('AbstractSource', ''),
                    'url': data.get('AbstractURL', '')
                }
            
            # Try Answer (calculations, conversions)
            if data.get('Answer'):
                return {
                    'success': True,
                    'answer': data['Answer'],
                    'source': 'DuckDuckGo Instant Answer',
                    'url': ''
                }
            
            # Try RelatedTopics
            if data.get('RelatedTopics'):
                topics = data['RelatedTopics'][:3]
                answer = '\n'.join(
                    t.get('Text', '') for t in topics if isinstance(t, dict) and t.get('Text')
                )
                if answer:
                    return {
                        'success': True,
                        'answer': answer,
                        'source': 'DuckDuckGo',
                        'url': ''
                    }
            
            return {'success': False, 'answer': '', 'source': '', 'url': ''}
            
        except Exception as e:
            return {'success': False, 'answer': str(e), 'source': '', 'url': ''}
