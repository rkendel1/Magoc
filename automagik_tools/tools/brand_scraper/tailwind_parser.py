"""
Tailwind CSS Parser - Extract and map Tailwind class names to CSS values
"""

import re
from typing import Dict, Any, Set, Optional
import httpx
from bs4 import BeautifulSoup


class TailwindParser:
    """Parse Tailwind CSS configurations and map utility classes to CSS values"""

    def __init__(self, timeout: int = 30, user_agent: str = ""):
        self.timeout = timeout
        self.user_agent = user_agent or "Mozilla/5.0 (compatible; BrandScraperBot/1.0)"

        # Default Tailwind color palette
        self.default_colors = {
            "slate": {
                "50": "#f8fafc",
                "100": "#f1f5f9",
                "200": "#e2e8f0",
                "300": "#cbd5e1",
                "400": "#94a3b8",
                "500": "#64748b",
                "600": "#475569",
                "700": "#334155",
                "800": "#1e293b",
                "900": "#0f172a",
                "950": "#020617",
            },
            "gray": {
                "50": "#f9fafb",
                "100": "#f3f4f6",
                "200": "#e5e7eb",
                "300": "#d1d5db",
                "400": "#9ca3af",
                "500": "#6b7280",
                "600": "#4b5563",
                "700": "#374151",
                "800": "#1f2937",
                "900": "#111827",
                "950": "#030712",
            },
            "primary": {"DEFAULT": "#3b82f6"},
            "secondary": {"DEFAULT": "#6b7280"},
        }

        # Common Tailwind spacing scale (in rem)
        self.spacing_scale = {
            "0": "0px",
            "1": "0.25rem",
            "2": "0.5rem",
            "3": "0.75rem",
            "4": "1rem",
            "5": "1.25rem",
            "6": "1.5rem",
            "8": "2rem",
            "10": "2.5rem",
            "12": "3rem",
            "16": "4rem",
            "20": "5rem",
            "24": "6rem",
        }

        # Font size mappings
        self.font_sizes = {
            "xs": "0.75rem",
            "sm": "0.875rem",
            "base": "1rem",
            "lg": "1.125rem",
            "xl": "1.25rem",
            "2xl": "1.5rem",
            "3xl": "1.875rem",
            "4xl": "2.25rem",
            "5xl": "3rem",
            "6xl": "3.75rem",
        }

    async def extract_tailwind_config(
        self, url: str, html_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract Tailwind configuration from a website

        Args:
            url: The URL to extract from
            html_content: Optional pre-fetched HTML content

        Returns:
            Dictionary with Tailwind configuration and detected classes
        """
        if not html_content:
            html_content = await self._fetch_page(url)

        soup = BeautifulSoup(html_content, "html.parser")

        # Extract Tailwind classes from HTML
        tailwind_classes = self._extract_tailwind_classes(soup)

        # Try to find and parse tailwind.config.js
        custom_config = await self._find_tailwind_config(url, soup)

        # Map classes to CSS values
        mapped_styles = self._map_classes_to_css(tailwind_classes, custom_config)

        return {
            "detected_classes": sorted(list(tailwind_classes)),
            "custom_config": custom_config,
            "mapped_styles": mapped_styles,
            "design_tokens": self._extract_design_tokens(mapped_styles, custom_config),
        }

    def _extract_tailwind_classes(self, soup: BeautifulSoup) -> Set[str]:
        """Extract Tailwind utility classes from HTML elements"""
        classes = set()

        # Common Tailwind patterns
        tailwind_patterns = [
            r"^(bg|text|border|rounded|p|m|px|py|mx|my|mt|mb|ml|mr|pt|pb|pl|pr|w|h|flex|grid|gap|font|leading|tracking)-",
            r"^(hover|focus|active|disabled|group-hover|sm|md|lg|xl|2xl):",
        ]

        # Find all elements with class attributes
        for element in soup.find_all(class_=True):
            element_classes = element.get("class", [])
            if isinstance(element_classes, str):
                element_classes = element_classes.split()

            for cls in element_classes:
                # Check if it matches Tailwind patterns
                for pattern in tailwind_patterns:
                    if re.match(pattern, cls):
                        classes.add(cls)
                        break

        return classes

    async def _find_tailwind_config(
        self, base_url: str, soup: BeautifulSoup
    ) -> Dict[str, Any]:
        """
        Try to find and parse tailwind.config.js

        Args:
            base_url: Base URL of the website
            soup: BeautifulSoup object of the page

        Returns:
            Parsed Tailwind configuration or empty dict
        """
        # Look for script tags that might contain config
        config_data = {}

        # Check for inline Tailwind configuration in script tags
        for script in soup.find_all("script"):
            script_text = script.string or ""
            if "tailwind.config" in script_text or "theme:" in script_text:
                # Try to extract configuration from inline script
                config_data = self._parse_inline_config(script_text)
                if config_data:
                    break

        return config_data

    def _parse_inline_config(self, script_text: str) -> Dict[str, Any]:
        """
        Parse inline Tailwind configuration from script text

        Args:
            script_text: JavaScript text potentially containing config

        Returns:
            Parsed configuration dictionary
        """
        config = {}

        # Try to extract theme colors - updated regex to handle nested objects
        colors_match = re.search(
            r"colors?\s*:\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}", script_text, re.DOTALL
        )
        if colors_match:
            colors_text = colors_match.group(1)
            # Parse color definitions - look for key: value patterns
            # Handle both 'brand-blue': '#1fb6ff' and brand-blue: '#1fb6ff'
            color_pairs = re.findall(
                r"['\"]?([a-zA-Z-]+)['\"]?\s*:\s*['\"]([^'\"]+)['\"]", colors_text
            )
            if color_pairs:
                config["colors"] = dict(color_pairs)

        # Try to extract theme fonts
        fonts_match = re.search(r"fontFamily\s*:\s*\{([^}]+)\}", script_text, re.DOTALL)
        if fonts_match:
            fonts_text = fonts_match.group(1)
            font_pairs = re.findall(r"(\w+)\s*:\s*\[([^\]]+)\]", fonts_text)
            if font_pairs:
                config["fonts"] = {
                    name: [f.strip().strip("'\"") for f in fonts.split(",")]
                    for name, fonts in font_pairs
                }

        return config

    def _map_classes_to_css(
        self, classes: Set[str], custom_config: Dict[str, Any]
    ) -> Dict[str, Dict[str, str]]:
        """
        Map Tailwind classes to actual CSS properties

        Args:
            classes: Set of Tailwind class names
            custom_config: Custom Tailwind configuration

        Returns:
            Dictionary mapping classes to CSS properties
        """
        mapped = {}

        # Merge custom colors with defaults
        colors = {**self.default_colors, **custom_config.get("colors", {})}

        for cls in classes:
            # Remove responsive/state prefixes for mapping
            base_class = re.sub(r"^(hover|focus|active|sm|md|lg|xl|2xl):", "", cls)

            css_props = {}

            # Background color mapping
            if base_class.startswith("bg-"):
                color_key = base_class[3:]
                css_props["background-color"] = self._resolve_color(color_key, colors)

            # Text color mapping
            elif base_class.startswith("text-"):
                parts = base_class[5:].split("-")
                if len(parts) >= 1:
                    # Could be color or size
                    if parts[0] in self.font_sizes:
                        css_props["font-size"] = self.font_sizes[parts[0]]
                    else:
                        color_key = base_class[5:]
                        css_props["color"] = self._resolve_color(color_key, colors)

            # Padding mapping
            elif (
                base_class.startswith("p-")
                or base_class.startswith("px-")
                or base_class.startswith("py-")
            ):
                spacing_value = self._extract_spacing_value(base_class)
                if spacing_value:
                    if base_class.startswith("px-"):
                        css_props["padding-left"] = spacing_value
                        css_props["padding-right"] = spacing_value
                    elif base_class.startswith("py-"):
                        css_props["padding-top"] = spacing_value
                        css_props["padding-bottom"] = spacing_value
                    else:
                        css_props["padding"] = spacing_value

            # Margin mapping
            elif (
                base_class.startswith("m-")
                or base_class.startswith("mx-")
                or base_class.startswith("my-")
            ):
                spacing_value = self._extract_spacing_value(base_class)
                if spacing_value:
                    if base_class.startswith("mx-"):
                        css_props["margin-left"] = spacing_value
                        css_props["margin-right"] = spacing_value
                    elif base_class.startswith("my-"):
                        css_props["margin-top"] = spacing_value
                        css_props["margin-bottom"] = spacing_value
                    else:
                        css_props["margin"] = spacing_value

            # Font weight
            elif base_class.startswith("font-"):
                weight = base_class[5:]
                weight_map = {
                    "thin": "100",
                    "light": "300",
                    "normal": "400",
                    "medium": "500",
                    "semibold": "600",
                    "bold": "700",
                    "extrabold": "800",
                    "black": "900",
                }
                if weight in weight_map:
                    css_props["font-weight"] = weight_map[weight]

            # Rounded corners
            elif base_class.startswith("rounded"):
                rounded_map = {
                    "rounded": "0.25rem",
                    "rounded-sm": "0.125rem",
                    "rounded-md": "0.375rem",
                    "rounded-lg": "0.5rem",
                    "rounded-xl": "0.75rem",
                    "rounded-2xl": "1rem",
                    "rounded-full": "9999px",
                }
                if base_class in rounded_map:
                    css_props["border-radius"] = rounded_map[base_class]

            if css_props:
                mapped[cls] = css_props

        return mapped

    def _resolve_color(self, color_key: str, colors: Dict[str, Any]) -> Optional[str]:
        """
        Resolve a Tailwind color key to an actual color value

        Args:
            color_key: Color key like "primary", "blue-500", etc.
            colors: Color configuration

        Returns:
            Hex color value or None
        """
        # Handle color-shade format (e.g., "blue-500")
        parts = color_key.split("-")

        if len(parts) == 1:
            # Simple color name
            if parts[0] in colors:
                color_config = colors[parts[0]]
                if isinstance(color_config, dict):
                    return color_config.get("DEFAULT") or color_config.get("500")
                return color_config
        elif len(parts) == 2:
            # Color with shade
            color_name, shade = parts
            if color_name in colors and isinstance(colors[color_name], dict):
                return colors[color_name].get(shade)

        return None

    def _extract_spacing_value(self, class_name: str) -> Optional[str]:
        """Extract spacing value from Tailwind spacing class"""
        # Extract number from class like "p-4", "px-2", "my-8"
        match = re.search(r"-(\d+)$", class_name)
        if match:
            spacing_key = match.group(1)
            return self.spacing_scale.get(spacing_key)
        return None

    def _extract_design_tokens(
        self, mapped_styles: Dict[str, Dict[str, str]], custom_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract design tokens from mapped styles

        Args:
            mapped_styles: Mapped Tailwind classes to CSS
            custom_config: Custom Tailwind configuration

        Returns:
            Design tokens organized by category
        """
        tokens = {
            "colors": set(),
            "spacing": set(),
            "typography": {"font_sizes": set(), "font_weights": set()},
        }

        for css_props in mapped_styles.values():
            if "background-color" in css_props and css_props["background-color"]:
                tokens["colors"].add(css_props["background-color"])
            if "color" in css_props and css_props["color"]:
                tokens["colors"].add(css_props["color"])

            for prop, value in css_props.items():
                if value is None:
                    continue
                if prop in [
                    "padding",
                    "margin",
                    "padding-left",
                    "padding-right",
                    "margin-left",
                    "margin-right",
                ]:
                    tokens["spacing"].add(value)
                elif prop == "font-size":
                    tokens["typography"]["font_sizes"].add(value)
                elif prop == "font-weight":
                    tokens["typography"]["font_weights"].add(value)

        # Convert sets to sorted lists, filtering out None values
        tokens["colors"] = sorted([c for c in tokens["colors"] if c is not None])
        tokens["spacing"] = sorted([s for s in tokens["spacing"] if s is not None])
        tokens["typography"]["font_sizes"] = sorted(
            [f for f in tokens["typography"]["font_sizes"] if f is not None]
        )
        tokens["typography"]["font_weights"] = sorted(
            [w for w in tokens["typography"]["font_weights"] if w is not None]
        )

        # Add custom theme colors if available
        if "colors" in custom_config:
            tokens["custom_theme_colors"] = custom_config["colors"]

        # Add custom fonts if available
        if "fonts" in custom_config:
            tokens["typography"]["custom_fonts"] = custom_config["fonts"]

        return tokens

    async def _fetch_page(self, url: str) -> str:
        """Fetch page content via HTTP"""
        async with httpx.AsyncClient(
            timeout=self.timeout, follow_redirects=True
        ) as client:
            headers = {"User-Agent": self.user_agent}
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
