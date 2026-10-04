from langchain.tools import tool
import requests
from dotenv import load_dotenv
import os
from tavily import TavilyClient
from rich import print
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from readability import Document
import trafilatura
import re


load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


@tool
def web_search(query: str) -> str:
    """Search the web for recent and reliable information on a topic. Returns titles, URLs and content snippets."""
    results = tavily.search(query=query, max_results=5)
    out = []

    for r in results['results']:
        out.append(
            f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['content'][:300]}\n"
        )

    return "\n------\n".join(out)

def scrape_url(url: str) -> str:
    """
    Extract clean, readable text from a URL.
    Try article content, main content, then the page body.
    """
    url = url.strip()
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("Enter a complete HTTP or HTTPS URL.")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,text/plain",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=(10, 30),
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Could not fetch {url}: {exc}") from exc

    content_type = response.headers.get("Content-Type", "").lower()

    if "text/plain" in content_type:
        return response.text.strip()

    if content_type and not any(
        value in content_type
        for value in ("text/html", "application/xhtml+xml")
    ):
        raise ValueError(f"Unsupported content type: {content_type}")

    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""

    for element in soup.select(
        "script, style, noscript, template, "
        "nav, footer, aside, form, iframe"
    ):
        element.decompose()

    candidates = soup.select("article")

    if not candidates:
        candidates = soup.select("main, [role='main']")

    if not candidates:
        candidates = [soup.body or soup]

    content = max(
        candidates,
        key=lambda element: len(element.get_text(" ", strip=True)),
    )

    raw_text = content.get_text(separator="\n", strip=True)

    lines = [
        " ".join(line.split())
        for line in raw_text.splitlines()
        if line.strip()
    ]

    text = "\n".join(lines)

    if not text:
        raise ValueError("No readable text found on this page.")

    return f"{title}\n\n{text}" if title else text
    