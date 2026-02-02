"""Web search service for finding relevant information on the internet."""

import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime
import httpx
from duckduckgo_search import AsyncDDGS

from app.models.data_source import DataSource
from app.models.collected_data import CollectedData, DataFormat


class WebSearchService:
    """Service for web search integration."""

    def __init__(self, serpapi_key: Optional[str] = None):
        """
        Initialize web search service.

        Args:
            serpapi_key: Optional SerpAPI key for enhanced search
        """
        self.serpapi_key = serpapi_key
        self.timeout = 30.0
        self.rate_limit_delay = 1.0

    async def search_duckduckgo(
        self,
        query: str,
        max_results: int = 10,
        region: str = "ru-ru",
        safesearch: str = "moderate",
    ) -> List[Dict[str, Any]]:
        """
        Search using DuckDuckGo (free, no API key required).

        Args:
            query: Search query
            max_results: Maximum number of results
            region: Region code (e.g., "ru-ru", "us-en")
            safesearch: Safe search level ("on", "moderate", "off")

        Returns:
            List of search result dictionaries
        """
        try:
            await asyncio.sleep(self.rate_limit_delay)

            async with AsyncDDGS() as ddgs:
                results = []
                async for result in ddgs.text(
                    query,
                    region=region,
                    safesearch=safesearch,
                    max_results=max_results,
                ):
                    results.append({
                        "title": result.get("title", ""),
                        "url": result.get("href", ""),
                        "snippet": result.get("body", ""),
                        "source": "duckduckgo",
                    })

                return results

        except Exception as e:
            print(f"DuckDuckGo search error for query '{query}': {e}")
            return []

    async def search_news_duckduckgo(
        self,
        query: str,
        max_results: int = 10,
        region: str = "ru-ru",
    ) -> List[Dict[str, Any]]:
        """
        Search news using DuckDuckGo.

        Args:
            query: Search query
            max_results: Maximum number of results
            region: Region code

        Returns:
            List of news result dictionaries
        """
        try:
            await asyncio.sleep(self.rate_limit_delay)

            async with AsyncDDGS() as ddgs:
                results = []
                async for result in ddgs.news(
                    query,
                    region=region,
                    max_results=max_results,
                ):
                    results.append({
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "snippet": result.get("body", ""),
                        "date": result.get("date", ""),
                        "source": result.get("source", ""),
                    })

                return results

        except Exception as e:
            print(f"DuckDuckGo news search error for query '{query}': {e}")
            return []

    async def search_serpapi(
        self,
        query: str,
        max_results: int = 10,
        search_type: str = "google",
        country: str = "ru",
        language: str = "ru",
    ) -> List[Dict[str, Any]]:
        """
        Search using SerpAPI (requires API key).

        Args:
            query: Search query
            max_results: Maximum number of results
            search_type: Search engine type ("google", "yandex", "bing")
            country: Country code
            language: Language code

        Returns:
            List of search result dictionaries
        """
        if not self.serpapi_key:
            print("SerpAPI key not configured, skipping SerpAPI search")
            return []

        try:
            await asyncio.sleep(self.rate_limit_delay)

            url = "https://serpapi.com/search"
            params = {
                "api_key": self.serpapi_key,
                "q": query,
                "num": max_results,
                "engine": search_type,
                "gl": country,
                "hl": language,
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                results = []
                organic_results = data.get("organic_results", [])

                for result in organic_results[:max_results]:
                    results.append({
                        "title": result.get("title", ""),
                        "url": result.get("link", ""),
                        "snippet": result.get("snippet", ""),
                        "source": "serpapi",
                        "position": result.get("position"),
                    })

                return results

        except httpx.HTTPStatusError as e:
            print(f"SerpAPI HTTP error for query '{query}': {e}")
            return []
        except Exception as e:
            print(f"SerpAPI search error for query '{query}': {e}")
            return []

    async def search_with_fallback(
        self,
        query: str,
        max_results: int = 10,
        prefer_serpapi: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Search with automatic fallback (SerpAPI -> DuckDuckGo or vice versa).

        Args:
            query: Search query
            max_results: Maximum number of results
            prefer_serpapi: If True, try SerpAPI first, otherwise start with DuckDuckGo

        Returns:
            List of search result dictionaries
        """
        if prefer_serpapi and self.serpapi_key:
            # Try SerpAPI first
            results = await self.search_serpapi(query, max_results)
            if results:
                return results
            # Fallback to DuckDuckGo
            return await self.search_duckduckgo(query, max_results)
        else:
            # Try DuckDuckGo first
            results = await self.search_duckduckgo(query, max_results)
            if results:
                return results
            # Fallback to SerpAPI if available
            if self.serpapi_key:
                return await self.search_serpapi(query, max_results)
            return []

    async def search_competitors(
        self,
        industry: str,
        region: str,
        product_keywords: List[str],
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Search for competitor information.

        Args:
            industry: Industry/sector
            region: Region/location
            product_keywords: Keywords related to the product
            max_results: Maximum number of results

        Returns:
            List of competitor-related search results
        """
        # Build search queries for competitors
        queries = [
            f"{industry} компании {region}",
            f"{industry} лидеры рынка {region}",
            f"{' '.join(product_keywords[:3])} производители {region}",
            f"конкуренты {industry} {region}",
        ]

        all_results = []
        for query in queries:
            results = await self.search_with_fallback(
                query,
                max_results=max(5, max_results // len(queries)),
            )
            all_results.extend(results)

        # Remove duplicates based on URL
        seen_urls = set()
        unique_results = []
        for result in all_results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)

        return unique_results[:max_results]

    async def search_industry_news(
        self,
        industry: str,
        region: str,
        max_results: int = 20,
        days_back: int = 90,
    ) -> List[Dict[str, Any]]:
        """
        Search for industry-specific news.

        Args:
            industry: Industry/sector
            region: Region/location
            max_results: Maximum number of results
            days_back: How many days back to search

        Returns:
            List of news results
        """
        # Build news queries
        queries = [
            f"{industry} новости {region}",
            f"{industry} тренды {region}",
            f"{industry} рынок {region}",
        ]

        all_news = []
        for query in queries:
            news = await self.search_news_duckduckgo(
                query,
                max_results=max(5, max_results // len(queries)),
            )
            all_news.extend(news)

        # Remove duplicates
        seen_urls = set()
        unique_news = []
        for item in all_news:
            url = item.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_news.append(item)

        return unique_news[:max_results]

    async def search_market_data(
        self,
        industry: str,
        region: str,
        keywords: List[str],
        max_results: int = 15,
    ) -> List[Dict[str, Any]]:
        """
        Search for market data and statistics.

        Args:
            industry: Industry/sector
            region: Region/location
            keywords: Additional search keywords
            max_results: Maximum number of results

        Returns:
            List of market data results
        """
        queries = [
            f"{industry} статистика {region}",
            f"{industry} объем рынка {region}",
            f"{industry} аналитика {region}",
            f"{' '.join(keywords[:2])} рынок данные {region}",
        ]

        all_results = []
        for query in queries:
            results = await self.search_with_fallback(
                query,
                max_results=max(4, max_results // len(queries)),
            )
            all_results.extend(results)

        # Remove duplicates
        seen_urls = set()
        unique_results = []
        for result in all_results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)

        return unique_results[:max_results]

    def convert_to_collected_data(
        self,
        search_results: List[Dict[str, Any]],
        source: Optional[DataSource] = None,
        research_id: Optional[str] = None,
    ) -> List[CollectedData]:
        """
        Convert search results to CollectedData objects.

        Args:
            search_results: List of search result dictionaries
            source: DataSource object if available
            research_id: Research ID if available

        Returns:
            List of CollectedData objects
        """
        collected_data_list = []

        for result in search_results:
            title = result.get("title", "No title")
            snippet = result.get("snippet", "")
            url = result.get("url", "")

            # Create text content from result
            content = f"Title: {title}\n\nURL: {url}\n\nSnippet: {snippet}"

            collected_data = CollectedData(
                source_id=source.id if source else None,
                research_id=research_id,
                title=title,
                raw_content=str(result),
                processed_content=content,
                format=DataFormat.TEXT,
                source_url=url,
                collected_date=datetime.utcnow(),
                size_bytes=len(content.encode("utf-8")),
                extra_metadata={
                    "search_source": result.get("source", "unknown"),
                    "snippet": snippet,
                    "date": result.get("date"),
                    "position": result.get("position"),
                },
                is_processed="no",
            )

            collected_data_list.append(collected_data)

        return collected_data_list

    async def comprehensive_search(
        self,
        industry: str,
        region: str,
        product_description: str,
        max_results_per_category: int = 10,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Perform comprehensive search across multiple categories.

        Args:
            industry: Industry/sector
            region: Region/location
            product_description: Product description for keyword extraction
            max_results_per_category: Max results per category

        Returns:
            Dictionary with categorized search results
        """
        # Extract keywords from product description (simple word extraction)
        keywords = [
            word for word in product_description.split()
            if len(word) > 3 and word.isalnum()
        ][:10]

        # Run searches in parallel
        results = await asyncio.gather(
            self.search_competitors(industry, region, keywords, max_results_per_category),
            self.search_industry_news(industry, region, max_results_per_category),
            self.search_market_data(industry, region, keywords, max_results_per_category),
            return_exceptions=True,
        )

        return {
            "competitors": results[0] if not isinstance(results[0], Exception) else [],
            "news": results[1] if not isinstance(results[1], Exception) else [],
            "market_data": results[2] if not isinstance(results[2], Exception) else [],
        }
