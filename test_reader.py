import re
from browser_agent.reader import PageReader

clauses = ["read https://example.com", "summarize this page https://news.ycombinator.com"]
for c in clauses:
    m = re.match(r'(?:read|summarize|open and read|what does .+ say)\s+(?:this\s+)?(?:page|article|website|url)?\s*(.+)', c)
    if m:
        url = m.group(1).strip()
        print(f"Matched URL: {url}")
        res = PageReader.read_page(url)
        print(res['success'], res['title'], len(res.get('text', '')))
    else:
        print("No match")
