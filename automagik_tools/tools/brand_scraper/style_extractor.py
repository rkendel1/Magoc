"""
Style Extractor - Extract CSS, colors, fonts, and design tokens from web pages
"""

import re
from typing import Dict, Any, List, Set, Optional
import httpx
from bs4 import BeautifulSoup


class StyleExtractor:
    """Extract design tokens and CSS from web pages"""

    def __init__(self, timeout: int = 30, user_agent: str = ""):
        self.timeout = timeout
        self.user_agent = user_agent or "Mozilla/5.0 (compatible; BrandScraperBot/1.0)"

    async def extract(
        self, url: str, html_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract design tokens from a URL or HTML content

        Args:
            url: The URL to extract from
            html_content: Optional pre-fetched HTML content

        Returns:
            Dictionary with extracted design tokens
        """
        if not html_content:
            html_content = await self._fetch_page(url)

        soup = BeautifulSoup(html_content, "html.parser")

        colors = self._extract_colors(soup, html_content)
        fonts = self._extract_fonts(soup, html_content)
        css_variables = self._extract_css_variables(html_content)
        typography = self._extract_typography(soup)

        return {
            "colors": colors,
            "fonts": fonts,
            "css_variables": css_variables,
            "typography": typography,
            "metadata": {
                "url": url,
                "title": self._get_title(soup),
            },
        }

    async def _fetch_page(self, url: str) -> str:
        """Fetch page content via HTTP"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = {"User-Agent": self.user_agent}
            response = await client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            return response.text

    def _extract_colors(
        self, soup: BeautifulSoup, html_content: str
    ) -> Dict[str, List[str]]:
        """Extract color values from CSS and inline styles"""
        colors: Set[str] = set()

        # Extract from inline styles
        for element in soup.find_all(style=True):
            style = element.get("style", "")
            colors.update(self._find_colors_in_text(style))

        # Extract from style tags
        for style_tag in soup.find_all("style"):
            colors.update(self._find_colors_in_text(style_tag.string or ""))

        # Extract from full HTML (catches external CSS that might be inlined)
        colors.update(self._find_colors_in_text(html_content))

        # Categorize colors
        hex_colors = [c for c in colors if c.startswith("#")]
        rgb_colors = [c for c in colors if c.startswith("rgb")]
        named_colors = [
            c for c in colors if not c.startswith("#") and not c.startswith("rgb")
        ]

        return {
            "hex": sorted(list(set(hex_colors)))[:50],  # Limit to 50 most common
            "rgb": sorted(list(set(rgb_colors)))[:50],
            "named": sorted(list(set(named_colors)))[:20],
            "primary": self._identify_primary_colors(list(colors)),
        }

    def _find_colors_in_text(self, text: str) -> Set[str]:
        """Find color values in text using regex"""
        colors = set()

        # Hex colors
        hex_pattern = r"#(?:[0-9a-fA-F]{3}){1,2}\b"
        colors.update(re.findall(hex_pattern, text))

        # RGB/RGBA colors
        rgb_pattern = r"rgba?\([^)]+\)"
        colors.update(re.findall(rgb_pattern, text))

        # Named colors (common web colors)
        named_colors = [
            "black",
            "white",
            "red",
            "green",
            "blue",
            "yellow",
            "purple",
            "orange",
            "pink",
            "brown",
            "gray",
            "grey",
            "navy",
            "teal",
            "cyan",
            "magenta",
        ]
        for color in named_colors:
            if re.search(r"\b" + color + r"\b", text, re.IGNORECASE):
                colors.add(color.lower())

        return colors

    def _identify_primary_colors(self, colors: List[str]) -> List[str]:
        """Identify most likely primary brand colors"""
        # Simple heuristic: most frequently appearing colors
        # In a real implementation, this could use color frequency analysis
        return sorted(list(set(colors)))[:5]

    def _extract_fonts(self, soup: BeautifulSoup, html_content: str) -> Dict[str, Any]:
        """Extract font families and typography information"""
        fonts: Set[str] = set()

        # Extract from inline styles
        for element in soup.find_all(style=True):
            style = element.get("style", "")
            fonts.update(self._find_fonts_in_text(style))

        # Extract from style tags
        for style_tag in soup.find_all("style"):
            fonts.update(self._find_fonts_in_text(style_tag.string or ""))

        # Extract from HTML
        fonts.update(self._find_fonts_in_text(html_content))

        # Look for Google Fonts or font CDN links
        font_links = []
        for link in soup.find_all("link", href=True):
            href = link.get("href", "")
            # Use proper URL parsing to validate domain
            try:
                from urllib.parse import urlparse

                parsed = urlparse(href)
                # Only allow HTTPS and check exact hostname
                if parsed.scheme == "https" and parsed.hostname in [
                    "fonts.googleapis.com",
                    "fonts.adobe.com",
                ]:
                    font_links.append(href)
            except ValueError:
                # Skip malformed URLs
                continue

        return {
            "families": sorted(list(fonts)),
            "font_links": font_links,
            "system_fonts": self._categorize_system_fonts(list(fonts)),
        }

    def _find_fonts_in_text(self, text: str) -> Set[str]:
        """Find font-family declarations in CSS text"""
        fonts = set()

        # Match font-family declarations
        font_pattern = r"font-family:\s*([^;]+);"
        matches = re.findall(font_pattern, text, re.IGNORECASE)

        for match in matches:
            # Clean up font names
            font_list = [f.strip().strip("\"'") for f in match.split(",")]
            fonts.update(font_list)

        return fonts

    def _categorize_system_fonts(self, fonts: List[str]) -> Dict[str, List[str]]:
        """Categorize fonts into system, serif, sans-serif, etc."""
        system = [
            "system-ui",
            "Arial",
            "Helvetica",
            "Times New Roman",
            "Georgia",
            "Courier",
        ]
        serif_fonts = []
        sans_serif_fonts = []
        custom_fonts = []

        for font in fonts:
            font_lower = font.lower()
            if any(sys_font.lower() in font_lower for sys_font in system):
                continue
            elif "serif" in font_lower and "sans" not in font_lower:
                serif_fonts.append(font)
            elif "sans" in font_lower or font.lower() in ["arial", "helvetica"]:
                sans_serif_fonts.append(font)
            else:
                custom_fonts.append(font)

        return {
            "serif": serif_fonts,
            "sans_serif": sans_serif_fonts,
            "custom": custom_fonts,
        }

    def _extract_css_variables(self, html_content: str) -> Dict[str, str]:
        """Extract CSS custom properties (variables)"""
        variables = {}

        # Find CSS variables (--variable-name: value)
        var_pattern = r"--([a-zA-Z0-9-_]+):\s*([^;]+);"
        matches = re.findall(var_pattern, html_content)

        for var_name, var_value in matches:
            variables[f"--{var_name}"] = var_value.strip()

        return variables

    def _extract_typography(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract typography scale and heading styles"""
        headings = {}

        for level in range(1, 7):
            heading_tag = f"h{level}"
            heading = soup.find(heading_tag)
            if heading:
                headings[heading_tag] = {
                    "text": heading.get_text()[:100],  # First 100 chars
                    "style": heading.get("style", ""),
                }

        return {
            "headings": headings,
            "body_text_sample": self._get_body_text_sample(soup),
        }

    def _get_body_text_sample(self, soup: BeautifulSoup) -> str:
        """Get sample of body text"""
        paragraphs = soup.find_all("p")
        if paragraphs:
            return paragraphs[0].get_text()[:200]
        return ""

    def _get_title(self, soup: BeautifulSoup) -> str:
        """Get page title"""
        title_tag = soup.find("title")
        return title_tag.get_text() if title_tag else ""
