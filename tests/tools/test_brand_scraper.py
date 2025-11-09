"""
Tests for Brand Scraper tool
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from automagik_tools.tools.brand_scraper import (
    create_server,
    get_metadata,
    get_config_class,
)
from automagik_tools.tools.brand_scraper.config import BrandScraperConfig
from automagik_tools.tools.brand_scraper.client import BrandScraperClient
from automagik_tools.tools.brand_scraper.style_extractor import StyleExtractor
from automagik_tools.tools.brand_scraper.image_extractor import ImageExtractor
from automagik_tools.tools.brand_scraper.tone_analyzer import ToneAnalyzer


# Sample HTML for testing
SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Brand Site</title>
    <link rel="icon" href="/favicon.ico">
    <meta property="og:image" content="https://example.com/og-image.jpg">
    <style>
        :root {
            --primary-color: #007bff;
            --secondary-color: #6c757d;
        }
        body {
            font-family: 'Roboto', Arial, sans-serif;
            color: #333;
            background-color: white;
        }
        h1 {
            font-size: 32px;
            color: #007bff;
        }
    </style>
</head>
<body>
    <header>
        <img src="/logo.png" alt="Company Logo" class="logo" width="200" height="100">
    </header>
    <main>
        <h1>Welcome to Our Amazing Platform</h1>
        <p>We are excited to help you build innovative solutions. Our team is committed to providing the best experience.</p>
        <p>Join thousands of happy customers who trust our platform every day.</p>
    </main>
</body>
</html>
"""


class TestBrandScraperConfig:
    """Test BrandScraperConfig"""

    def test_config_creation(self):
        """Test creating config with defaults"""
        config = BrandScraperConfig()
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.extract_styles is True
        assert config.extract_images is True
        assert config.extract_tone is True

    def test_config_with_custom_values(self):
        """Test creating config with custom values"""
        config = BrandScraperConfig(
            timeout=60, max_retries=5, max_images=50, extract_styles=False
        )
        assert config.timeout == 60
        assert config.max_retries == 5
        assert config.max_images == 50
        assert config.extract_styles is False


class TestStyleExtractor:
    """Test StyleExtractor"""

    @pytest.mark.asyncio
    async def test_extract_colors(self):
        """Test color extraction from HTML"""
        extractor = StyleExtractor()
        result = await extractor.extract("https://example.com", SAMPLE_HTML)

        assert "colors" in result
        colors = result["colors"]
        assert "hex" in colors
        assert "rgb" in colors

        # Should find the colors in our sample HTML
        assert any("#007bff" in c for c in colors["hex"])
        assert any("#6c757d" in c for c in colors["hex"])

    @pytest.mark.asyncio
    async def test_extract_fonts(self):
        """Test font extraction from HTML"""
        extractor = StyleExtractor()
        result = await extractor.extract("https://example.com", SAMPLE_HTML)

        assert "fonts" in result
        fonts = result["fonts"]
        assert "families" in fonts

        # Should find Roboto font from sample
        assert any("Roboto" in f for f in fonts["families"])

    @pytest.mark.asyncio
    async def test_extract_css_variables(self):
        """Test CSS variable extraction"""
        extractor = StyleExtractor()
        result = await extractor.extract("https://example.com", SAMPLE_HTML)

        assert "css_variables" in result
        css_vars = result["css_variables"]

        # Should find CSS custom properties
        assert "--primary-color" in css_vars or "--primary-color:" in str(css_vars)

    @pytest.mark.asyncio
    async def test_extract_typography(self):
        """Test typography extraction"""
        extractor = StyleExtractor()
        result = await extractor.extract("https://example.com", SAMPLE_HTML)

        assert "typography" in result
        typography = result["typography"]
        assert "headings" in typography


class TestImageExtractor:
    """Test ImageExtractor"""

    @pytest.mark.asyncio
    async def test_extract_logos(self):
        """Test logo extraction from HTML"""
        extractor = ImageExtractor()
        result = await extractor.extract("https://example.com", SAMPLE_HTML)

        assert "logos" in result
        logos = result["logos"]

        # Should find logo image
        assert len(logos) > 0
        assert any("/logo.png" in logo.get("url", "") for logo in logos)

    @pytest.mark.asyncio
    async def test_extract_favicons(self):
        """Test favicon extraction"""
        extractor = ImageExtractor()
        result = await extractor.extract("https://example.com", SAMPLE_HTML)

        assert "favicons" in result
        favicons = result["favicons"]

        # Should find favicon
        assert len(favicons) > 0

    @pytest.mark.asyncio
    async def test_extract_og_images(self):
        """Test Open Graph image extraction"""
        extractor = ImageExtractor()
        result = await extractor.extract("https://example.com", SAMPLE_HTML)

        assert "og_images" in result
        og_images = result["og_images"]

        # Should find OG image
        assert len(og_images) > 0
        assert any("og-image.jpg" in img.get("url", "") for img in og_images)

    @pytest.mark.asyncio
    async def test_make_absolute_url(self):
        """Test URL absolutization"""
        extractor = ImageExtractor()

        # Test relative URL
        absolute = extractor._make_absolute_url("/logo.png", "https://example.com/page")
        assert absolute == "https://example.com/logo.png"

        # Test already absolute URL
        absolute = extractor._make_absolute_url(
            "https://cdn.example.com/image.jpg", "https://example.com"
        )
        assert absolute == "https://cdn.example.com/image.jpg"

        # Test protocol-relative URL
        absolute = extractor._make_absolute_url(
            "//cdn.example.com/image.jpg", "https://example.com"
        )
        assert absolute == "https://cdn.example.com/image.jpg"


class TestToneAnalyzer:
    """Test ToneAnalyzer"""

    @pytest.mark.asyncio
    async def test_analyze_tone(self):
        """Test tone analysis"""
        analyzer = ToneAnalyzer()
        result = await analyzer.extract("https://example.com", SAMPLE_HTML)

        assert "tone" in result
        tone = result["tone"]
        assert "scores" in tone
        assert "dominant" in tone

    @pytest.mark.asyncio
    async def test_sentiment_analysis(self):
        """Test sentiment analysis"""
        analyzer = ToneAnalyzer()
        result = await analyzer.extract("https://example.com", SAMPLE_HTML)

        assert "sentiment" in result
        sentiment = result["sentiment"]
        assert "sentiment" in sentiment
        assert "score" in sentiment

        # Our sample has positive words, should be positive or neutral
        assert sentiment["sentiment"] in ["positive", "neutral"]

    @pytest.mark.asyncio
    async def test_characteristics_analysis(self):
        """Test text characteristics analysis"""
        analyzer = ToneAnalyzer()
        result = await analyzer.extract("https://example.com", SAMPLE_HTML)

        assert "characteristics" in result
        chars = result["characteristics"]
        assert "avg_word_length" in chars
        assert "avg_sentence_length" in chars


class TestBrandScraperClient:
    """Test BrandScraperClient"""

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test client initialization"""
        config = BrandScraperConfig()
        client = BrandScraperClient(config)

        assert client.config == config
        assert isinstance(client.style_extractor, StyleExtractor)
        assert isinstance(client.image_extractor, ImageExtractor)
        assert isinstance(client.tone_analyzer, ToneAnalyzer)

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_scrape_brand(self, mock_client):
        """Test comprehensive brand scraping"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.text = SAMPLE_HTML
        mock_response.raise_for_status = Mock()

        mock_http = AsyncMock()
        mock_http.get.return_value = mock_response
        mock_http.__aenter__.return_value = mock_http
        mock_http.__aexit__.return_value = None

        mock_client.return_value = mock_http

        config = BrandScraperConfig()
        client = BrandScraperClient(config)

        result = await client.scrape_brand("https://example.com")

        assert result["status"] == "success"
        assert result["url"] == "https://example.com"
        assert "design_tokens" in result
        assert "images" in result
        assert "voice_tone" in result


class TestMCPTool:
    """Test MCP tool integration"""

    def test_create_server(self):
        """Test MCP server creation"""
        server = create_server()
        assert server is not None

    def test_get_metadata(self):
        """Test metadata retrieval"""
        metadata = get_metadata()
        assert metadata["name"] == "brand-scraper"
        assert "version" in metadata
        assert "description" in metadata

    def test_get_config_class(self):
        """Test config class retrieval"""
        config_class = get_config_class()
        assert config_class == BrandScraperConfig

    @pytest.mark.asyncio
    async def test_tool_functions_exist(self):
        """Test that MCP tool functions are properly exposed"""
        from automagik_tools.tools.brand_scraper import (
            scrape_brand,
            extract_design_tokens,
            extract_images,
            analyze_tone,
            scrape_and_store,
            batch_scrape,
        )

        # Verify functions exist (FastMCP wraps them, so they're not directly callable)
        assert scrape_brand is not None
        assert extract_design_tokens is not None
        assert extract_images is not None
        assert analyze_tone is not None
        assert scrape_and_store is not None
        assert batch_scrape is not None


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_empty_html(self):
        """Test handling of empty HTML"""
        extractor = StyleExtractor()
        # Provide HTML content directly to avoid network call
        result = await extractor.extract("https://example.com", "<html></html>")

        # Should not crash, return empty results
        assert "colors" in result
        assert "fonts" in result

    @pytest.mark.asyncio
    async def test_malformed_html(self):
        """Test handling of malformed HTML"""
        malformed = "<html><body><p>Unclosed paragraph"
        extractor = StyleExtractor()

        # Should handle gracefully
        result = await extractor.extract("https://example.com", malformed)
        assert result is not None

    @pytest.mark.asyncio
    async def test_invalid_url_format(self):
        """Test handling of invalid URLs"""
        config = BrandScraperConfig()
        client = BrandScraperClient(config)

        result = await client.scrape_brand("not-a-valid-url")

        # Should return error status
        assert result["status"] == "error"
        assert "error" in result
