"""
Brand Scraper Configuration
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class BrandScraperConfig(BaseSettings):
    """Configuration for Brand Scraper tool"""

    model_config = SettingsConfigDict(
        env_prefix="BRAND_SCRAPER_",
        env_file=".env",
        extra="ignore"
    )

    # API Configuration
    convex_url: str = Field(
        default="", 
        description="Convex backend URL for storing extracted data"
    )
    
    convex_api_key: str = Field(
        default="", 
        description="Convex API authentication key"
    )

    # Scraper Configuration
    timeout: int = Field(
        default=30, 
        description="Timeout for HTTP requests in seconds"
    )

    max_retries: int = Field(
        default=3, 
        description="Maximum number of retry attempts"
    )

    use_selenium: bool = Field(
        default=False,
        description="Use Selenium for JavaScript-heavy sites"
    )

    user_agent: str = Field(
        default="Mozilla/5.0 (compatible; BrandScraperBot/1.0)",
        description="User agent for HTTP requests"
    )

    # Extraction Configuration
    extract_styles: bool = Field(default=True, description="Extract CSS and design tokens")
    extract_images: bool = Field(default=True, description="Extract logos and images")
    extract_tone: bool = Field(default=True, description="Analyze voice and tone")
    
    max_images: int = Field(
        default=20,
        description="Maximum number of images to extract"
    )

    max_text_length: int = Field(
        default=10000,
        description="Maximum text length for tone analysis"
    )
