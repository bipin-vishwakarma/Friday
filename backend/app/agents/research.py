"""
Web Research Agent
Performs free real-time internet search and info retrieval without paid APIs.
Uses DuckDuckGo and Wikipedia instant summaries.
"""

import httpx
import logging
import urllib.parse
from typing import Dict, Any

logger = logging.getLogger("friday.research")

class ResearchAgent:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    async def search(self, query: str) -> Dict[str, Any]:
        """Perform free instant web search."""
        logger.info(f"Researching query: {query}")
        clean_query = query.strip()
        
        # 1. Try DuckDuckGo Instant Answer API (completely free JSON)
        try:
            url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(clean_query)}&format=json&no_html=1&skip_disambig=1"
            async with httpx.AsyncClient(timeout=6.0, headers=self.headers) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    abstract = data.get("AbstractText", "")
                    heading = data.get("Heading", "")
                    if abstract:
                        return {
                            "status": "success",
                            "summary": f"{heading}: {abstract}" if heading else abstract,
                            "source": data.get("AbstractURL", "DuckDuckGo")
                        }
                    
                    # Check related topics
                    related = data.get("RelatedTopics", [])
                    if related and isinstance(related[0], dict) and "Text" in related[0]:
                        return {
                            "status": "success",
                            "summary": related[0]["Text"],
                            "source": related[0].get("FirstURL", "DuckDuckGo")
                        }
        except Exception as e:
            logger.debug(f"DuckDuckGo API error: {e}")

        # 2. Try Wikipedia summary API (free JSON)
        try:
            wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(clean_query)}"
            async with httpx.AsyncClient(timeout=6.0, headers=self.headers) as client:
                resp = await client.get(wiki_url)
                if resp.status_code == 200:
                    data = resp.json()
                    extract = data.get("extract")
                    if extract:
                        return {
                            "status": "success",
                            "summary": extract,
                            "source": data.get("content_urls", {}).get("desktop", {}).get("page", "Wikipedia")
                        }
        except Exception as e:
            logger.debug(f"Wikipedia summary error: {e}")

        return {
            "status": "fallback",
            "summary": f"I couldn't find a direct instant answer for '{clean_query}', but I have opened your default browser to search for it.",
            "source": f"https://www.google.com/search?q={urllib.parse.quote(clean_query)}"
        }
