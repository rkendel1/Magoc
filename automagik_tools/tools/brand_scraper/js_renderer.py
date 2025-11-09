"""
JavaScript Renderer - Render JavaScript-heavy websites using Playwright
"""

import asyncio
import logging
from typing import Dict, Any
from contextlib import asynccontextmanager


logger = logging.getLogger(__name__)


class JavaScriptRenderer:
    """Render JavaScript-heavy websites using Playwright"""

    def __init__(
        self,
        timeout: int = 30,
        user_agent: str = "",
        headless: bool = True,
        enable_detailed_logging: bool = True,
    ):
        self.timeout = timeout
        self.user_agent = user_agent or "Mozilla/5.0 (compatible; BrandScraperBot/1.0)"
        self.headless = headless
        self.enable_detailed_logging = enable_detailed_logging
        self._playwright = None
        self._browser = None

        # Check if Playwright is available
        self._playwright_available = self._check_playwright_available()

    def _check_playwright_available(self) -> bool:
        """Check if Playwright is installed and available"""
        try:
            import playwright  # noqa: F401

            return True
        except ImportError:
            if self.enable_detailed_logging:
                logger.warning(
                    "Playwright not installed. Install with: pip install playwright && playwright install chromium"
                )
            return False

    @asynccontextmanager
    async def _get_browser(self):
        """Get or create browser instance"""
        if not self._playwright_available:
            raise RuntimeError(
                "Playwright is not available. Install with: pip install playwright && playwright install chromium"
            )

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=self.headless)
                try:
                    yield browser
                finally:
                    await browser.close()
        except Exception as e:
            if self.enable_detailed_logging:
                logger.error(f"Failed to launch Playwright browser: {e}")
            raise

    async def render(self, url: str) -> Dict[str, Any]:
        """
        Render a URL and return the content

        Args:
            url: The URL to render

        Returns:
            Dictionary with rendered HTML and metadata
        """
        if not self._playwright_available:
            raise RuntimeError(
                "Playwright is not available. Install with: pip install playwright && playwright install chromium"
            )

        try:
            async with self._get_browser() as browser:
                context = await browser.new_context(user_agent=self.user_agent)
                page = await context.new_page()

                # Navigate to URL
                if self.enable_detailed_logging:
                    logger.info(f"Rendering URL with Playwright: {url}")

                try:
                    response = await page.goto(
                        url, wait_until="networkidle", timeout=self.timeout * 1000
                    )

                    # Wait for any dynamic content to load
                    await page.wait_for_load_state("networkidle")

                    # Get rendered HTML
                    html_content = await page.content()

                    # Get page title
                    title = await page.title()

                    # Get any console errors
                    console_errors = []

                    # Setup console listener for future renders
                    def on_console(msg):
                        if msg.type == "error":
                            console_errors.append(msg.text)

                    page.on("console", on_console)

                    # Take a screenshot for debugging if needed
                    screenshot = None
                    try:
                        screenshot_bytes = await page.screenshot(full_page=False)
                        screenshot = screenshot_bytes
                    except Exception as e:
                        if self.enable_detailed_logging:
                            logger.warning(f"Failed to take screenshot: {e}")

                    await context.close()

                    return {
                        "status": "success",
                        "url": url,
                        "html": html_content,
                        "title": title,
                        "status_code": response.status if response else None,
                        "console_errors": console_errors,
                        "screenshot": screenshot,
                        "renderer": "playwright",
                    }

                except Exception as e:
                    if self.enable_detailed_logging:
                        logger.error(f"Error rendering URL {url}: {e}")
                    raise

        except Exception as e:
            if self.enable_detailed_logging:
                logger.error(f"Failed to render {url} with Playwright: {e}")
            return {
                "status": "error",
                "url": url,
                "error": str(e),
                "error_type": type(e).__name__,
                "renderer": "playwright",
            }

    async def render_with_actions(
        self, url: str, actions: list[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Render a URL with custom actions (click, scroll, wait, etc.)

        Args:
            url: The URL to render
            actions: List of actions to perform (e.g., [{"type": "click", "selector": "#button"}])

        Returns:
            Dictionary with rendered HTML and metadata
        """
        if not self._playwright_available:
            raise RuntimeError("Playwright is not available")

        actions = actions or []

        try:
            async with self._get_browser() as browser:
                context = await browser.new_context(user_agent=self.user_agent)
                page = await context.new_page()

                await page.goto(
                    url, wait_until="networkidle", timeout=self.timeout * 1000
                )

                # Perform actions
                for action in actions:
                    action_type = action.get("type")
                    if action_type == "click":
                        selector = action.get("selector")
                        if selector:
                            await page.click(selector)
                            await page.wait_for_load_state("networkidle")
                    elif action_type == "scroll":
                        await page.evaluate(
                            "window.scrollTo(0, document.body.scrollHeight)"
                        )
                        await asyncio.sleep(1)
                    elif action_type == "wait":
                        wait_time = action.get("time", 1)
                        await asyncio.sleep(wait_time)

                html_content = await page.content()
                title = await page.title()

                await context.close()

                return {
                    "status": "success",
                    "url": url,
                    "html": html_content,
                    "title": title,
                    "actions_performed": len(actions),
                    "renderer": "playwright",
                }

        except Exception as e:
            if self.enable_detailed_logging:
                logger.error(f"Failed to render {url} with actions: {e}")
            return {
                "status": "error",
                "url": url,
                "error": str(e),
                "error_type": type(e).__name__,
                "renderer": "playwright",
            }

    def is_available(self) -> bool:
        """Check if Playwright renderer is available"""
        return self._playwright_available
