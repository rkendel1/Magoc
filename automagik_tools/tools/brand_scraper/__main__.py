"""
Brand Scraper CLI runner
"""

from .config import BrandScraperConfig
from . import create_server

config = BrandScraperConfig()
mcp = create_server(config)
