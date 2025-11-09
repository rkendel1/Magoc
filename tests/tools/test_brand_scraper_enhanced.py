"""
Tests for enhanced Brand Scraper functionality (Tailwind, JS rendering)
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from automagik_tools.tools.brand_scraper.config import BrandScraperConfig
from automagik_tools.tools.brand_scraper.tailwind_parser import TailwindParser
from automagik_tools.tools.brand_scraper.js_renderer import JavaScriptRenderer
from automagik_tools.tools.brand_scraper.selenium_renderer import SeleniumRenderer
from automagik_tools.tools.brand_scraper.client import BrandScraperClient


# Sample HTML with Tailwind classes
TAILWIND_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Tailwind Test Site</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        'brand-blue': '#1fb6ff',
                        'brand-purple': '#7e5bef',
                    }
                }
            }
        }
    </script>
</head>
<body class="bg-gray-100">
    <div class="container mx-auto px-4">
        <h1 class="text-4xl font-bold text-brand-blue">Welcome</h1>
        <p class="text-gray-700 mt-4 mb-6">This is a Tailwind-powered site.</p>
        <button class="bg-brand-purple hover:bg-purple-700 text-white font-bold py-2 px-4 rounded">
            Click Me
        </button>
    </div>
</body>
</html>
"""


class TestBrandScraperEnhancedConfig:
    """Test enhanced configuration options"""

    def test_config_with_new_options(self):
        """Test creating config with new options"""
        config = BrandScraperConfig(
            enable_playwright=True,
            selenium_fallback=True,
            js_rendering_enabled=True,
            use_tailwind_mapping=True,
            enable_detailed_logging=True,
            fallback_on_js_error=True,
        )
        assert config.enable_playwright is True
        assert config.selenium_fallback is True
        assert config.js_rendering_enabled is True
        assert config.use_tailwind_mapping is True
        assert config.enable_detailed_logging is True
        assert config.fallback_on_js_error is True

    def test_config_default_values(self):
        """Test default values for new config options"""
        config = BrandScraperConfig()
        assert config.enable_playwright is True
        assert config.selenium_fallback is False
        assert config.js_rendering_enabled is True
        assert config.use_tailwind_mapping is True
        assert config.js_rendering_timeout == 30


class TestTailwindParser:
    """Test Tailwind CSS parser"""

    @pytest.mark.asyncio
    async def test_extract_tailwind_classes(self):
        """Test Tailwind class extraction"""
        parser = TailwindParser()
        result = await parser.extract_tailwind_config(
            "https://example.com", TAILWIND_HTML
        )

        assert "detected_classes" in result
        classes = result["detected_classes"]

        # Should find Tailwind utility classes
        assert any("bg-" in cls for cls in classes)
        assert any("text-" in cls for cls in classes)
        assert any("font-" in cls for cls in classes)
        assert any("px-" in cls or "py-" in cls for cls in classes)

    @pytest.mark.asyncio
    async def test_extract_custom_config(self):
        """Test custom Tailwind config extraction"""
        parser = TailwindParser()
        result = await parser.extract_tailwind_config(
            "https://example.com", TAILWIND_HTML
        )

        assert "custom_config" in result
        config = result["custom_config"]

        # Should extract custom colors from inline config
        assert "colors" in config
        assert "brand-blue" in config["colors"]
        assert config["colors"]["brand-blue"] == "#1fb6ff"

    @pytest.mark.asyncio
    async def test_map_classes_to_css(self):
        """Test mapping Tailwind classes to CSS"""
        parser = TailwindParser()
        result = await parser.extract_tailwind_config(
            "https://example.com", TAILWIND_HTML
        )

        assert "mapped_styles" in result
        mapped = result["mapped_styles"]

        # Check some mappings exist
        assert len(mapped) > 0

        # Verify CSS properties are mapped
        for class_name, css_props in mapped.items():
            assert isinstance(css_props, dict)
            # Each mapping should have at least one CSS property
            assert len(css_props) > 0

    @pytest.mark.asyncio
    async def test_extract_design_tokens(self):
        """Test design token extraction from Tailwind"""
        parser = TailwindParser()
        result = await parser.extract_tailwind_config(
            "https://example.com", TAILWIND_HTML
        )

        assert "design_tokens" in result
        tokens = result["design_tokens"]

        # Should have color tokens
        assert "colors" in tokens
        assert isinstance(tokens["colors"], list)

        # Should have typography tokens
        assert "typography" in tokens
        assert "font_sizes" in tokens["typography"]

    @pytest.mark.asyncio
    async def test_color_resolution(self):
        """Test Tailwind color resolution"""
        parser = TailwindParser()

        # Test default color resolution
        color = parser._resolve_color("blue-500", parser.default_colors)
        assert color is None or isinstance(color, str)

        # Test custom color resolution
        custom_colors = {"primary": {"DEFAULT": "#123456"}}
        color = parser._resolve_color("primary", custom_colors)
        assert color == "#123456"

    @pytest.mark.asyncio
    async def test_spacing_extraction(self):
        """Test spacing value extraction"""
        parser = TailwindParser()

        # Test spacing extraction
        assert parser._extract_spacing_value("p-4") == "1rem"
        assert parser._extract_spacing_value("px-2") == "0.5rem"
        assert parser._extract_spacing_value("my-8") == "2rem"


class TestJavaScriptRenderer:
    """Test JavaScript renderer with Playwright"""

    def test_renderer_initialization(self):
        """Test JS renderer initialization"""
        renderer = JavaScriptRenderer(timeout=30)
        assert renderer.timeout == 30
        # is_available() checks if Playwright is installed
        # Will be False in CI unless Playwright is installed
        assert isinstance(renderer.is_available(), bool)

    def test_playwright_availability_check(self):
        """Test Playwright availability detection"""
        renderer = JavaScriptRenderer()
        # Should not crash even if Playwright is not installed
        is_available = renderer._check_playwright_available()
        assert isinstance(is_available, bool)

    @pytest.mark.asyncio
    async def test_render_without_playwright(self):
        """Test render behavior when Playwright is unavailable"""
        renderer = JavaScriptRenderer()

        if not renderer.is_available():
            # Should raise RuntimeError when Playwright is not available
            with pytest.raises(RuntimeError, match="Playwright is not available"):
                await renderer.render("https://example.com")


class TestSeleniumRenderer:
    """Test Selenium renderer as fallback"""

    def test_renderer_initialization(self):
        """Test Selenium renderer initialization"""
        renderer = SeleniumRenderer(timeout=30)
        assert renderer.timeout == 30
        # is_available() checks if Selenium is installed
        assert isinstance(renderer.is_available(), bool)

    def test_selenium_availability_check(self):
        """Test Selenium availability detection"""
        renderer = SeleniumRenderer()
        # Should not crash even if Selenium is not installed
        is_available = renderer._check_selenium_available()
        assert isinstance(is_available, bool)

    @pytest.mark.asyncio
    async def test_render_without_selenium(self):
        """Test render behavior when Selenium is unavailable"""
        renderer = SeleniumRenderer()

        if not renderer.is_available():
            # Should raise RuntimeError when Selenium is not available
            with pytest.raises(RuntimeError, match="Selenium is not available"):
                await renderer.render("https://example.com")


class TestEnhancedBrandScraperClient:
    """Test enhanced Brand Scraper client with new features"""

    @pytest.mark.asyncio
    async def test_client_with_tailwind_enabled(self):
        """Test client initialization with Tailwind enabled"""
        config = BrandScraperConfig(use_tailwind_mapping=True)
        client = BrandScraperClient(config)

        assert client.tailwind_parser is not None

    @pytest.mark.asyncio
    async def test_client_with_js_rendering_disabled(self):
        """Test client with JS rendering disabled"""
        config = BrandScraperConfig(js_rendering_enabled=False)
        client = BrandScraperClient(config)

        assert client.js_renderer is None
        assert client.selenium_renderer is None

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_scrape_with_tailwind(self, mock_client):
        """Test scraping with Tailwind extraction"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.text = TAILWIND_HTML
        mock_response.raise_for_status = Mock()

        mock_http = AsyncMock()
        mock_http.get.return_value = mock_response
        mock_http.__aenter__.return_value = mock_http
        mock_http.__aexit__.return_value = None

        mock_client.return_value = mock_http

        config = BrandScraperConfig(
            use_tailwind_mapping=True, js_rendering_enabled=False
        )
        client = BrandScraperClient(config)

        result = await client.scrape_brand("https://example.com")

        assert result["status"] == "success"
        assert "tailwind" in result
        assert "detected_classes" in result["tailwind"]
        assert "design_tokens" in result

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_fetch_page_with_fallback(self, mock_client):
        """Test page fetching with fallback logic"""
        mock_response = Mock()
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.raise_for_status = Mock()

        mock_http = AsyncMock()
        mock_http.get.return_value = mock_response
        mock_http.__aenter__.return_value = mock_http
        mock_http.__aexit__.return_value = None

        mock_client.return_value = mock_http

        config = BrandScraperConfig(
            js_rendering_enabled=True,
            enable_playwright=False,
            selenium_fallback=False,
            fallback_on_js_error=True,
        )
        client = BrandScraperClient(config)

        html, method = await client._fetch_page_with_rendering("https://example.com")

        assert html is not None
        assert method == "static_fallback"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_error_handling_with_logging(self, mock_client):
        """Test error handling with detailed logging"""
        mock_http = AsyncMock()
        mock_http.get.side_effect = Exception("Network error")
        mock_http.__aenter__.return_value = mock_http
        mock_http.__aexit__.return_value = None

        mock_client.return_value = mock_http

        config = BrandScraperConfig(
            enable_detailed_logging=True, js_rendering_enabled=False
        )
        client = BrandScraperClient(config)

        result = await client.scrape_brand("https://example.com")

        assert result["status"] == "error"
        assert "error" in result
        assert "error_type" in result


class TestIntegration:
    """Integration tests for enhanced functionality"""

    @pytest.mark.asyncio
    async def test_full_scrape_with_all_features(self):
        """Test full scrape with all enhanced features enabled"""
        config = BrandScraperConfig(
            use_tailwind_mapping=True,
            js_rendering_enabled=False,  # Disable for testing
            extract_styles=True,
            extract_images=True,
            extract_tone=True,
        )
        client = BrandScraperClient(config)

        # Verify all components are initialized
        assert client.style_extractor is not None
        assert client.image_extractor is not None
        assert client.tone_analyzer is not None
        assert client.tailwind_parser is not None

    @pytest.mark.asyncio
    async def test_tailwind_only_extraction(self):
        """Test Tailwind-only extraction workflow"""
        parser = TailwindParser()
        result = await parser.extract_tailwind_config(
            "https://example.com", TAILWIND_HTML
        )

        # Should have all expected keys
        assert "detected_classes" in result
        assert "custom_config" in result
        assert "mapped_styles" in result
        assert "design_tokens" in result

        # Should extract meaningful data
        assert len(result["detected_classes"]) > 0
        assert len(result["mapped_styles"]) > 0
