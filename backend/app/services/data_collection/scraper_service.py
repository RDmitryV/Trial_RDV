"""Web scraping service for data collection."""

import asyncio
from typing import Optional, Dict, List
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from app.models.data_source import DataSource, SourceStatus
from app.models.collected_data import CollectedData, DataFormat


class ScraperService:
    """Service for web scraping."""

    def __init__(self):
        """Initialize scraper service."""
        self.user_agent = UserAgent()
        self.rate_limit_delay = 2.0  # seconds between requests
        self.timeout = 30.0  # request timeout in seconds

    def get_headers(self) -> Dict[str, str]:
        """Get headers for HTTP requests with rotating user agent."""
        return {
            "User-Agent": self.user_agent.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def fetch_url(
        self,
        url: str,
        source: Optional[DataSource] = None,
    ) -> Optional[CollectedData]:
        """
        Fetch content from a URL.

        Args:
            url: URL to fetch
            source: DataSource object if available

        Returns:
            CollectedData object or None if failed
        """
        try:
            # Respect rate limiting
            await asyncio.sleep(self.rate_limit_delay)

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self.get_headers(), follow_redirects=True)
                response.raise_for_status()

                # Parse HTML content
                soup = BeautifulSoup(response.text, "lxml")

                # Extract title
                title_tag = soup.find("title")
                title = title_tag.get_text().strip() if title_tag else None

                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.extract()

                # Get text content
                text_content = soup.get_text()

                # Clean up whitespace
                lines = (line.strip() for line in text_content.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text_content = "\n".join(chunk for chunk in chunks if chunk)

                # Create collected data object
                collected_data = CollectedData(
                    source_id=source.id if source else None,
                    title=title,
                    raw_content=response.text,
                    processed_content=text_content,
                    format=DataFormat.HTML,
                    source_url=url,
                    collected_date=datetime.utcnow(),
                    size_bytes=len(response.content),
                    extra_metadata={
                        "status_code": response.status_code,
                        "content_type": response.headers.get("content-type"),
                        "final_url": str(response.url),
                    },
                    is_processed="no",
                )

                # Update source status if provided
                if source:
                    source.last_successful_fetch = datetime.utcnow()
                    source.status = SourceStatus.ACTIVE

                return collected_data

        except httpx.HTTPStatusError as e:
            if source:
                source.last_failed_fetch = datetime.utcnow()
                source.status = SourceStatus.FAILED
            print(f"HTTP error fetching {url}: {e}")
            return None

        except httpx.RequestError as e:
            if source:
                source.last_failed_fetch = datetime.utcnow()
                source.status = SourceStatus.FAILED
            print(f"Request error fetching {url}: {e}")
            return None

        except Exception as e:
            if source:
                source.last_failed_fetch = datetime.utcnow()
                source.status = SourceStatus.FAILED
            print(f"Unexpected error fetching {url}: {e}")
            return None

    async def fetch_multiple_urls(
        self,
        urls: List[str],
        sources: Optional[List[DataSource]] = None,
    ) -> List[CollectedData]:
        """
        Fetch content from multiple URLs concurrently.

        Args:
            urls: List of URLs to fetch
            sources: Optional list of corresponding DataSource objects

        Returns:
            List of CollectedData objects
        """
        if sources and len(sources) != len(urls):
            raise ValueError("Length of sources must match length of urls")

        tasks = []
        for i, url in enumerate(urls):
            source = sources[i] if sources else None
            tasks.append(self.fetch_url(url, source))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out None and exceptions
        collected_data = []
        for result in results:
            if isinstance(result, CollectedData):
                collected_data.append(result)

        return collected_data

    def extract_links(self, html_content: str, base_url: str) -> List[str]:
        """
        Extract all links from HTML content.

        Args:
            html_content: HTML content as string
            base_url: Base URL for resolving relative links

        Returns:
            List of absolute URLs
        """
        soup = BeautifulSoup(html_content, "lxml")
        links = []

        for link in soup.find_all("a", href=True):
            href = link["href"]
            # Convert relative URLs to absolute
            if href.startswith("/"):
                from urllib.parse import urljoin
                href = urljoin(base_url, href)
            if href.startswith("http"):
                links.append(href)

        return list(set(links))  # Remove duplicates

    def extract_metadata(self, html_content: str) -> Dict[str, Optional[str]]:
        """
        Extract metadata from HTML content.

        Args:
            html_content: HTML content as string

        Returns:
            Dictionary with metadata (title, description, keywords, etc.)
        """
        soup = BeautifulSoup(html_content, "lxml")

        metadata = {
            "title": None,
            "description": None,
            "keywords": None,
            "author": None,
            "og_title": None,
            "og_description": None,
            "og_image": None,
        }

        # Extract title
        title_tag = soup.find("title")
        if title_tag:
            metadata["title"] = title_tag.get_text().strip()

        # Extract meta tags
        for meta in soup.find_all("meta"):
            name = meta.get("name", "").lower()
            property_attr = meta.get("property", "").lower()
            content = meta.get("content", "")

            if name == "description":
                metadata["description"] = content
            elif name == "keywords":
                metadata["keywords"] = content
            elif name == "author":
                metadata["author"] = content
            elif property_attr == "og:title":
                metadata["og_title"] = content
            elif property_attr == "og:description":
                metadata["og_description"] = content
            elif property_attr == "og:image":
                metadata["og_image"] = content

        return metadata
