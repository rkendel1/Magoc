"""
Brand Scraper Client - Orchestrates all extraction operations
"""

import httpx
import logging
from typing import Dict, Any
from .config import BrandScraperConfig
from .style_extractor import StyleExtractor
from .image_extractor import ImageExtractor
from .tone_analyzer import ToneAnalyzer
from .tailwind_parser import TailwindParser
from .js_renderer import JavaScriptRenderer
from .selenium_renderer import SeleniumRenderer

logger = logging.getLogger(__name__)


class BrandScraperClient:
    """Client for comprehensive brand scraping operations"""

    def __init__(self, config: BrandScraperConfig):
        self.config = config

        # Initialize extractors
        self.style_extractor = StyleExtractor(
            timeout=config.timeout, user_agent=config.user_agent
        )
        self.image_extractor = ImageExtractor(
            timeout=config.timeout,
            user_agent=config.user_agent,
            max_images=config.max_images,
        )
        self.tone_analyzer = ToneAnalyzer(
            timeout=config.timeout,
            user_agent=config.user_agent,
            max_text_length=config.max_text_length,
        )

        # Initialize Tailwind parser if enabled
        self.tailwind_parser = None
        if config.use_tailwind_mapping:
            self.tailwind_parser = TailwindParser(
                timeout=config.timeout, user_agent=config.user_agent
            )

        # Initialize JavaScript renderers if enabled
        self.js_renderer = None
        self.selenium_renderer = None

        if config.js_rendering_enabled:
            if config.enable_playwright:
                self.js_renderer = JavaScriptRenderer(
                    timeout=config.js_rendering_timeout,
                    user_agent=config.user_agent,
                    enable_detailed_logging=config.enable_detailed_logging,
                )

            if config.selenium_fallback:
                self.selenium_renderer = SeleniumRenderer(
                    timeout=config.js_rendering_timeout,
                    user_agent=config.user_agent,
                    enable_detailed_logging=config.enable_detailed_logging,
                )

    async def scrape_brand(self, url: str) -> Dict[str, Any]:
        """
        Comprehensive brand scraping from a URL

        Extracts:
        - Design tokens (colors, fonts, CSS variables)
        - Tailwind classes and mappings (if enabled)
        - Images and logos
        - Voice and tone analysis

        Args:
            url: The URL to scrape

        Returns:
            Dictionary with all extracted brand data
        """
        try:
            # Fetch page content (with JS rendering if enabled)
            html_content, render_method = await self._fetch_page_with_rendering(url)

            # Run all extractors
            results = {
                "url": url,
                "status": "success",
                "render_method": render_method,
            }

            # Extract styles if enabled
            if self.config.extract_styles:
                try:
                    results["design_tokens"] = await self.style_extractor.extract(
                        url, html_content
                    )
                except Exception as e:
                    if self.config.enable_detailed_logging:
                        logger.error(f"Style extraction failed for {url}: {e}")
                    results["design_tokens"] = {"error": str(e)}

            # Extract Tailwind classes if enabled
            if self.config.use_tailwind_mapping and self.tailwind_parser:
                try:
                    results["tailwind"] = (
                        await self.tailwind_parser.extract_tailwind_config(
                            url, html_content
                        )
                    )
                except Exception as e:
                    if self.config.enable_detailed_logging:
                        logger.error(f"Tailwind extraction failed for {url}: {e}")
                    results["tailwind"] = {"error": str(e)}

            # Extract images if enabled
            if self.config.extract_images:
                try:
                    results["images"] = await self.image_extractor.extract(
                        url, html_content
                    )
                except Exception as e:
                    if self.config.enable_detailed_logging:
                        logger.error(f"Image extraction failed for {url}: {e}")
                    results["images"] = {"error": str(e)}

            # Analyze tone if enabled
            if self.config.extract_tone:
                try:
                    results["voice_tone"] = await self.tone_analyzer.extract(
                        url, html_content
                    )
                except Exception as e:
                    if self.config.enable_detailed_logging:
                        logger.error(f"Tone analysis failed for {url}: {e}")
                    results["voice_tone"] = {"error": str(e)}

            return results

        except Exception as e:
            if self.config.enable_detailed_logging:
                logger.error(f"Brand scraping failed for {url}: {e}")
            return {
                "url": url,
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
            }

    async def _fetch_page_with_rendering(self, url: str) -> tuple[str, str]:
        """
        Fetch page content with JavaScript rendering if enabled

        Args:
            url: The URL to fetch

        Returns:
            Tuple of (html_content, render_method)
        """
        # Try JavaScript rendering first if enabled
        if self.config.js_rendering_enabled:
            # Try Playwright first
            if self.js_renderer and self.js_renderer.is_available():
                try:
                    result = await self.js_renderer.render(url)
                    if result.get("status") == "success":
                        return result["html"], "playwright"
                    else:
                        if self.config.enable_detailed_logging:
                            logger.warning(
                                f"Playwright rendering failed: {result.get('error')}"
                            )
                except Exception as e:
                    if self.config.enable_detailed_logging:
                        logger.warning(f"Playwright rendering error: {e}")

            # Try Selenium fallback if enabled
            if self.selenium_renderer and self.selenium_renderer.is_available():
                try:
                    result = await self.selenium_renderer.render(url)
                    if result.get("status") == "success":
                        return result["html"], "selenium"
                    else:
                        if self.config.enable_detailed_logging:
                            logger.warning(
                                f"Selenium rendering failed: {result.get('error')}"
                            )
                except Exception as e:
                    if self.config.enable_detailed_logging:
                        logger.warning(f"Selenium rendering error: {e}")

            # Fallback to static HTML if configured
            if self.config.fallback_on_js_error:
                if self.config.enable_detailed_logging:
                    logger.info(f"Falling back to static HTML extraction for {url}")
                return await self._fetch_page(url), "static_fallback"
            else:
                raise RuntimeError(
                    "JavaScript rendering failed and fallback is disabled"
                )

        # Use static HTML fetching
        return await self._fetch_page(url), "static"

    async def _fetch_page(self, url: str) -> str:
        """Fetch page content with retries and improved error handling"""
        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                async with httpx.AsyncClient(
                    timeout=self.config.timeout, follow_redirects=True
                ) as client:
                    headers = {"User-Agent": self.config.user_agent}
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()
                    return response.text
            except Exception as e:
                last_error = e
                if self.config.enable_detailed_logging:
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.config.max_retries} failed for {url}: {e}"
                    )
                if attempt < self.config.max_retries - 1:
                    continue

        error_msg = f"Failed to fetch page after {self.config.max_retries} attempts: {last_error}"
        if self.config.enable_detailed_logging:
            logger.error(error_msg)
        raise last_error or Exception(error_msg)

    async def store_to_convex(self, brand_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store extracted brand data to Convex backend

        Args:
            brand_data: The extracted brand data to store

        Returns:
            Dictionary with storage status
        """
        if not self.config.convex_url or not self.config.convex_api_key:
            return {"status": "error", "error": "Convex configuration not provided"}

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                headers = {
                    "Authorization": f"Bearer {self.config.convex_api_key}",
                    "Content-Type": "application/json",
                }

                response = await client.post(
                    f"{self.config.convex_url}/api/brand_data",
                    json=brand_data,
                    headers=headers,
                )
                response.raise_for_status()

                return {"status": "success", "convex_response": response.json()}
        except Exception as e:
            return {"status": "error", "error": str(e)}

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

        return {**brand_data, "storage": storage_result}
