"""
Brand Scraper Client - Orchestrates all extraction operations
"""

import httpx
from typing import Dict, Any, Optional
from .config import BrandScraperConfig
from .style_extractor import StyleExtractor
from .image_extractor import ImageExtractor
from .tone_analyzer import ToneAnalyzer


class BrandScraperClient:
    """Client for comprehensive brand scraping operations"""

    def __init__(self, config: BrandScraperConfig):
        self.config = config
        
        # Initialize extractors
        self.style_extractor = StyleExtractor(
            timeout=config.timeout,
            user_agent=config.user_agent
        )
        self.image_extractor = ImageExtractor(
            timeout=config.timeout,
            user_agent=config.user_agent,
            max_images=config.max_images
        )
        self.tone_analyzer = ToneAnalyzer(
            timeout=config.timeout,
            user_agent=config.user_agent,
            max_text_length=config.max_text_length
        )

    async def scrape_brand(self, url: str) -> Dict[str, Any]:
        """
        Comprehensive brand scraping from a URL
        
        Extracts:
        - Design tokens (colors, fonts, CSS variables)
        - Images and logos
        - Voice and tone analysis
        
        Args:
            url: The URL to scrape
            
        Returns:
            Dictionary with all extracted brand data
        """
        try:
            # Fetch page once for all extractors
            html_content = await self._fetch_page(url)
            
            # Run all extractors
            results = {
                "url": url,
                "status": "success",
            }
            
            # Extract styles if enabled
            if self.config.extract_styles:
                try:
                    results["design_tokens"] = await self.style_extractor.extract(url, html_content)
                except Exception as e:
                    results["design_tokens"] = {"error": str(e)}
            
            # Extract images if enabled
            if self.config.extract_images:
                try:
                    results["images"] = await self.image_extractor.extract(url, html_content)
                except Exception as e:
                    results["images"] = {"error": str(e)}
            
            # Analyze tone if enabled
            if self.config.extract_tone:
                try:
                    results["voice_tone"] = await self.tone_analyzer.extract(url, html_content)
                except Exception as e:
                    results["voice_tone"] = {"error": str(e)}
            
            return results
            
        except Exception as e:
            return {
                "url": url,
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }

    async def _fetch_page(self, url: str) -> str:
        """Fetch page content with retries"""
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                async with httpx.AsyncClient(
                    timeout=self.config.timeout,
                    follow_redirects=True
                ) as client:
                    headers = {"User-Agent": self.config.user_agent}
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()
                    return response.text
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    continue
        
        raise last_error or Exception("Failed to fetch page")

    async def store_to_convex(self, brand_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store extracted brand data to Convex backend
        
        Args:
            brand_data: The extracted brand data to store
            
        Returns:
            Dictionary with storage status
        """
        if not self.config.convex_url or not self.config.convex_api_key:
            return {
                "status": "error",
                "error": "Convex configuration not provided"
            }
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                headers = {
                    "Authorization": f"Bearer {self.config.convex_api_key}",
                    "Content-Type": "application/json"
                }
                
                response = await client.post(
                    f"{self.config.convex_url}/api/brand_data",
                    json=brand_data,
                    headers=headers
                )
                response.raise_for_status()
                
                return {
                    "status": "success",
                    "convex_response": response.json()
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def scrape_and_store(self, url: str) -> Dict[str, Any]:
        """
        Scrape brand data and store to Convex in one operation
        
        Args:
            url: The URL to scrape
            
        Returns:
            Combined results of scraping and storage
        """
        # Scrape the brand
        brand_data = await self.scrape_brand(url)
        
        if brand_data.get("status") != "success":
            return brand_data
        
        # Store to Convex
        storage_result = await self.store_to_convex(brand_data)
        
        return {
            **brand_data,
            "storage": storage_result
        }
