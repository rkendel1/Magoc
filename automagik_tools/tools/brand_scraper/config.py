"""
Brand Scraper Configuration
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BrandScraperConfig(BaseSettings):
    """Configuration for Brand Scraper tool"""

    model_config = SettingsConfigDict(
        env_prefix="BRAND_SCRAPER_", env_file=".env", extra="ignore"
    )

    # API Configuration
    convex_url: str = Field(
        default="", description="Convex backend URL for storing extracted data"
    )

    convex_api_key: str = Field(default="", description="Convex API authentication key")

    # Scraper Configuration
    timeout: int = Field(default=30, description="Timeout for HTTP requests in seconds")

    max_retries: int = Field(default=3, description="Maximum number of retry attempts")

    use_selenium: bool = Field(
        default=False, description="Use Selenium for JavaScript-heavy sites"
    )

    user_agent: str = Field(
        default="Mozilla/5.0 (compatible; BrandScraperBot/1.0)",
        description="User agent for HTTP requests",
    )

    # JavaScript Rendering Configuration
    enable_playwright: bool = Field(
        default=True, description="Enable Playwright for JavaScript rendering"
    )

    selenium_fallback: bool = Field(
        default=False,
        description="Use Selenium as fallback when Playwright fails or unavailable",
    )

    js_rendering_enabled: bool = Field(
        default=True,
        description="Enable JavaScript rendering (requires Playwright or Selenium)",
    )

    js_rendering_timeout: int = Field(
        default=30, description="Timeout for JavaScript rendering in seconds"
    )

    # Tailwind Configuration
    use_tailwind_mapping: bool = Field(
        default=True, description="Enable Tailwind class-name to CSS mapping"
    )

    tailwind_config_paths: list[str] = Field(
        default_factory=lambda: ["tailwind.config.js", "tailwind.config.ts"],
        description="Paths to search for Tailwind configuration files",
    )

    # Extraction Configuration
    extract_styles: bool = Field(
        default=True, description="Extract CSS and design tokens"
    )
    extract_images: bool = Field(default=True, description="Extract logos and images")
    extract_tone: bool = Field(default=True, description="Analyze voice and tone")

    max_images: int = Field(
        default=20, description="Maximum number of images to extract"
    )

    max_text_length: int = Field(
        default=10000, description="Maximum text length for tone analysis"
    )

    # Error Handling Configuration
    enable_detailed_logging: bool = Field(
        default=True, description="Enable detailed error logging"
    )

    fallback_on_js_error: bool = Field(
        default=True,
        description="Fallback to static HTML extraction when JS rendering fails",
    )
