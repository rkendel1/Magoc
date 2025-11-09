"""
Selenium Renderer - Fallback renderer for JavaScript-heavy websites using Selenium
"""

import logging
from typing import Dict, Any
from contextlib import contextmanager


logger = logging.getLogger(__name__)


class SeleniumRenderer:
    """Render JavaScript-heavy websites using Selenium as a fallback"""

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

        # Check if Selenium is available
        self._selenium_available = self._check_selenium_available()

    def _check_selenium_available(self) -> bool:
        """Check if Selenium is installed and available"""
        try:
            from selenium import webdriver  # noqa: F401

            return True
        except ImportError:
            if self.enable_detailed_logging:
                logger.warning(
                    "Selenium not installed. Install with: pip install selenium"
                )
            return False

    @contextmanager
    def _get_driver(self):
        """Get or create Selenium WebDriver instance"""
        if not self._selenium_available:
            raise RuntimeError(
                "Selenium is not available. Install with: pip install selenium"
            )

        driver = None
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.common.exceptions import WebDriverException

            # Setup Chrome options
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument(f"user-agent={self.user_agent}")

            # Try to create driver
            try:
                driver = webdriver.Chrome(options=chrome_options)
                driver.set_page_load_timeout(self.timeout)
                driver.implicitly_wait(self.timeout)
                yield driver
            except WebDriverException as e:
                if self.enable_detailed_logging:
                    logger.error(f"Failed to create Chrome WebDriver: {e}")
                    logger.info(
                        "Trying to use Chrome with default chromedriver location..."
                    )
                # Try without explicit service
                driver = webdriver.Chrome(options=chrome_options)
                driver.set_page_load_timeout(self.timeout)
                yield driver

        except Exception as e:
            if self.enable_detailed_logging:
                logger.error(f"Failed to initialize Selenium WebDriver: {e}")
            raise
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    if self.enable_detailed_logging:
                        logger.warning(f"Error closing WebDriver: {e}")

    async def render(self, url: str) -> Dict[str, Any]:
        """
        Render a URL and return the content

        Args:
            url: The URL to render

        Returns:
            Dictionary with rendered HTML and metadata
        """
        if not self._selenium_available:
            raise RuntimeError(
                "Selenium is not available. Install with: pip install selenium"
            )

        try:
            with self._get_driver() as driver:
                if self.enable_detailed_logging:
                    logger.info(f"Rendering URL with Selenium: {url}")

                try:
                    # Navigate to URL
                    driver.get(url)

                    # Wait for page to load (implicit wait is set)
                    # Additional explicit wait for body element
                    from selenium.webdriver.common.by import By
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC

                    try:
                        WebDriverWait(driver, self.timeout).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                    except Exception:
                        pass  # Continue even if wait times out

                    # Get rendered HTML
                    html_content = driver.page_source

                    # Get page title
                    title = driver.title

                    # Get console logs if available
                    console_logs = []
                    try:
                        logs = driver.get_log("browser")
                        console_logs = [
                            log["message"]
                            for log in logs
                            if log.get("level") == "SEVERE"
                        ]
                    except Exception:
                        pass  # Console logs may not be available

                    # Take screenshot if possible
                    screenshot = None
                    try:
                        screenshot_bytes = driver.get_screenshot_as_png()
                        screenshot = screenshot_bytes
                    except Exception as e:
                        if self.enable_detailed_logging:
                            logger.warning(f"Failed to take screenshot: {e}")

                    return {
                        "status": "success",
                        "url": url,
                        "html": html_content,
                        "title": title,
                        "console_logs": console_logs,
                        "screenshot": screenshot,
                        "renderer": "selenium",
                    }

                except Exception as e:
                    if self.enable_detailed_logging:
                        logger.error(f"Error rendering URL {url}: {e}")
                    raise

        except Exception as e:
            if self.enable_detailed_logging:
                logger.error(f"Failed to render {url} with Selenium: {e}")
            return {
                "status": "error",
                "url": url,
                "error": str(e),
                "error_type": type(e).__name__,
                "renderer": "selenium",
            }

    async def render_with_scroll(
        self, url: str, scroll_count: int = 3
    ) -> Dict[str, Any]:
        """
        Render a URL with scrolling to load dynamic content

        Args:
            url: The URL to render
            scroll_count: Number of times to scroll down

        Returns:
            Dictionary with rendered HTML and metadata
        """
        if not self._selenium_available:
            raise RuntimeError("Selenium is not available")

        try:
            with self._get_driver() as driver:
                driver.get(url)

                # Wait for initial load
                import time
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC

                try:
                    WebDriverWait(driver, self.timeout).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                except Exception:
                    pass

                # Scroll down multiple times
                for i in range(scroll_count):
                    driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);"
                    )
                    time.sleep(1)  # Wait for content to load

                html_content = driver.page_source
                title = driver.title

                return {
                    "status": "success",
                    "url": url,
                    "html": html_content,
                    "title": title,
                    "scrolls_performed": scroll_count,
                    "renderer": "selenium",
                }

        except Exception as e:
            if self.enable_detailed_logging:
                logger.error(f"Failed to render {url} with scrolling: {e}")
            return {
                "status": "error",
                "url": url,
                "error": str(e),
                "error_type": type(e).__name__,
                "renderer": "selenium",
            }

    def is_available(self) -> bool:
        """Check if Selenium renderer is available"""
        return self._selenium_available
