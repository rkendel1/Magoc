"""
Image and Logo Extractor - Extract brand images and logos from web pages
"""

import base64
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup


class ImageExtractor:
    """Extract images, logos, and brand visuals from web pages"""

    def __init__(self, timeout: int = 30, user_agent: str = "", max_images: int = 20):
        self.timeout = timeout
        self.user_agent = user_agent or "Mozilla/5.0 (compatible; BrandScraperBot/1.0)"
        self.max_images = max_images

    async def extract(
        self, url: str, html_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract images and logos from a URL or HTML content

        Args:
            url: The URL to extract from
            html_content: Optional pre-fetched HTML content

        Returns:
            Dictionary with extracted images and logos
        """
        if not html_content:
            html_content = await self._fetch_page(url)

        soup = BeautifulSoup(html_content, "html.parser")

        # Extract different types of images
        logos = await self._extract_logos(soup, url)
        favicons = await self._extract_favicons(soup, url)
        og_images = await self._extract_og_images(soup, url)
        general_images = await self._extract_general_images(soup, url)

        return {
            "logos": logos,
            "favicons": favicons,
            "og_images": og_images,
            "general_images": general_images[: self.max_images],
            "metadata": {
                "url": url,
                "total_images_found": len(general_images),
            },
        }

    async def _fetch_page(self, url: str) -> str:
        """Fetch page content via HTTP"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = {"User-Agent": self.user_agent}
            response = await client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            return response.text

    async def _extract_logos(
        self, soup: BeautifulSoup, base_url: str
    ) -> List[Dict[str, str]]:
        """Extract logo images using common selectors and patterns"""
        logos = []

        # Common logo selectors
        logo_selectors = [
            'img[alt*="logo" i]',
            'img[class*="logo" i]',
            'img[id*="logo" i]',
            "a.logo img",
            ".logo img",
            "#logo img",
            "header img",
            ".header img",
            ".brand img",
            ".navbar-brand img",
        ]

        found_urls = set()

        for selector in logo_selectors:
            elements = soup.select(selector)
            for element in elements:
                src = element.get("src") or element.get("data-src")
                if src and src not in found_urls:
                    found_urls.add(src)
                    logos.append(
                        {
                            "url": self._make_absolute_url(src, base_url),
                            "alt": element.get("alt", ""),
                            "type": "logo",
                            "selector": selector,
                        }
                    )

        # Also check for SVG logos
        svg_elements = soup.find_all(
            "svg", class_=lambda x: x and "logo" in x.lower() if x else False
        )
        for svg in svg_elements[:5]:  # Limit SVG extraction
            logos.append(
                {
                    "url": None,
                    "alt": "SVG Logo",
                    "type": "svg_logo",
                    "svg_content": str(svg)[:1000],  # First 1000 chars
                }
            )

        return logos

    async def _extract_favicons(
        self, soup: BeautifulSoup, base_url: str
    ) -> List[Dict[str, str]]:
        """Extract favicon and app icons"""
        favicons = []

        # Look for favicon links
        favicon_selectors = [
            'link[rel="icon"]',
            'link[rel="shortcut icon"]',
            'link[rel="apple-touch-icon"]',
            'link[rel="apple-touch-icon-precomposed"]',
        ]

        for selector in favicon_selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get("href")
                if href:
                    favicons.append(
                        {
                            "url": self._make_absolute_url(href, base_url),
                            "type": (
                                element.get("rel", ["favicon"])[0]
                                if isinstance(element.get("rel"), list)
                                else element.get("rel", "favicon")
                            ),
                            "sizes": element.get("sizes", ""),
                        }
                    )

        # Default favicon location
        if not favicons:
            parsed = urlparse(base_url)
            default_favicon = f"{parsed.scheme}://{parsed.netloc}/favicon.ico"
            favicons.append(
                {
                    "url": default_favicon,
                    "type": "default_favicon",
                    "sizes": "",
                }
            )

        return favicons

    async def _extract_og_images(
        self, soup: BeautifulSoup, base_url: str
    ) -> List[Dict[str, str]]:
        """Extract Open Graph images (social media preview images)"""
        og_images = []

        # Open Graph image
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            og_images.append(
                {
                    "url": self._make_absolute_url(og_image.get("content"), base_url),
                    "type": "og_image",
                    "description": "Open Graph preview image",
                }
            )

        # Twitter card image
        twitter_image = soup.find("meta", attrs={"name": "twitter:image"})
        if twitter_image and twitter_image.get("content"):
            og_images.append(
                {
                    "url": self._make_absolute_url(
                        twitter_image.get("content"), base_url
                    ),
                    "type": "twitter_image",
                    "description": "Twitter card image",
                }
            )

        return og_images

    async def _extract_general_images(
        self, soup: BeautifulSoup, base_url: str
    ) -> List[Dict[str, str]]:
        """Extract general images from the page"""
        images = []

        img_tags = soup.find_all("img")

        for img in img_tags:
            src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
            if not src:
                continue

            # Skip very small images (likely tracking pixels or icons)
            width = img.get("width")
            height = img.get("height")
            if width and height:
                try:
                    if int(width) < 50 or int(height) < 50:
                        continue
                except (ValueError, TypeError):
                    pass

            images.append(
                {
                    "url": self._make_absolute_url(src, base_url),
                    "alt": img.get("alt", ""),
                    "title": img.get("title", ""),
                    "width": width,
                    "height": height,
                }
            )

        return images

    def _make_absolute_url(self, url: str, base_url: str) -> str:
        """Convert relative URLs to absolute URLs"""
        if not url:
            return ""

        # Handle data URLs
        if url.startswith("data:"):
            return url

        # Handle protocol-relative URLs
        if url.startswith("//"):
            parsed_base = urlparse(base_url)
            return f"{parsed_base.scheme}:{url}"

        # Handle absolute URLs
        if url.startswith("http://") or url.startswith("https://"):
            return url

        # Handle relative URLs
        return urljoin(base_url, url)

    async def download_image_as_base64(self, image_url: str) -> Optional[str]:
        """Download an image and convert to base64"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {"User-Agent": self.user_agent}
                response = await client.get(
                    image_url, headers=headers, follow_redirects=True
                )
                response.raise_for_status()

                # Convert to base64
                image_data = response.content
                base64_data = base64.b64encode(image_data).decode("utf-8")

                # Get content type
                content_type = response.headers.get("content-type", "image/png")

                return f"data:{content_type};base64,{base64_data}"
        except Exception:
            return None
