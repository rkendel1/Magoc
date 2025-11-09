# Brand Scraper Enhanced Features

## Overview

The Brand Scraper tool has been enhanced with powerful capabilities to handle modern JavaScript-heavy and Tailwind CSS-powered websites. These enhancements provide better extraction of design tokens, improved compatibility, and flexible configuration options.

## New Features

### 1. Tailwind CSS Class-Name Parsing

The brand scraper can now intelligently parse and map Tailwind CSS utility classes to their actual CSS values.

#### Capabilities

- **Automatic Class Detection**: Identifies Tailwind utility classes in HTML (e.g., `bg-primary`, `text-2xl`, `px-4`)
- **Custom Theme Support**: Extracts custom color themes and configuration from inline Tailwind configs
- **Design Token Extraction**: Maps utility classes to actual CSS values for colors, spacing, typography
- **Comprehensive Coverage**: Supports backgrounds, text colors, padding, margin, fonts, border-radius, and more

#### Usage

```python
from automagik_tools.tools.brand_scraper import BrandScraperClient, BrandScraperConfig

# Enable Tailwind mapping (enabled by default)
config = BrandScraperConfig(use_tailwind_mapping=True)
client = BrandScraperClient(config)

# Scrape a Tailwind-powered site
result = await client.scrape_brand("https://tailwindcss.com")

# Access Tailwind data
tailwind_data = result.get("tailwind", {})
print(f"Detected classes: {tailwind_data['detected_classes']}")
print(f"Mapped styles: {tailwind_data['mapped_styles']}")
print(f"Design tokens: {tailwind_data['design_tokens']}")
```

#### Extracted Data Structure

```json
{
  "tailwind": {
    "detected_classes": ["bg-blue-500", "text-white", "px-4", "py-2"],
    "custom_config": {
      "colors": {
        "brand-blue": "#1fb6ff",
        "brand-purple": "#7e5bef"
      }
    },
    "mapped_styles": {
      "bg-blue-500": {"background-color": "#3b82f6"},
      "text-white": {"color": "#ffffff"},
      "px-4": {"padding-left": "1rem", "padding-right": "1rem"}
    },
    "design_tokens": {
      "colors": ["#3b82f6", "#ffffff"],
      "spacing": ["1rem", "0.5rem"],
      "typography": {
        "font_sizes": ["1rem", "1.5rem"],
        "font_weights": ["400", "700"]
      }
    }
  }
}
```

### 2. JavaScript Rendering with Playwright

The brand scraper now supports rendering JavaScript-heavy websites using Playwright, ensuring accurate extraction from modern SPAs and dynamically generated content.

#### Capabilities

- **Full JavaScript Execution**: Renders pages with full JavaScript support
- **Wait for Content**: Automatically waits for network idle and dynamic content
- **Screenshot Capture**: Optionally captures screenshots for debugging
- **Console Error Tracking**: Captures JavaScript console errors
- **Custom Actions**: Supports clicks, scrolling, and other interactions

#### Installation

```bash
pip install playwright
playwright install chromium
```

#### Usage

```python
from automagik_tools.tools.brand_scraper import BrandScraperClient, BrandScraperConfig

# Enable Playwright (enabled by default when installed)
config = BrandScraperConfig(
    enable_playwright=True,
    js_rendering_enabled=True,
    js_rendering_timeout=30
)
client = BrandScraperClient(config)

# Scrape a JavaScript-heavy site
result = await client.scrape_brand("https://react-app.example.com")
print(f"Rendered with: {result['render_method']}")  # "playwright"
```

### 3. Selenium Fallback

For environments where Playwright is unavailable or when additional compatibility is needed, the brand scraper can fall back to Selenium.

#### Capabilities

- **Browser Compatibility**: Works in environments where Playwright may not be available
- **Automatic Fallback**: Seamlessly falls back when Playwright fails
- **Scroll Support**: Can perform multiple scrolls to load infinite-scroll content
- **Modular Design**: Can be enabled/disabled independently

#### Installation

```bash
pip install selenium
```

#### Usage

```python
from automagik_tools.tools.brand_scraper import BrandScraperClient, BrandScraperConfig

# Enable Selenium as fallback
config = BrandScraperConfig(
    enable_playwright=True,
    selenium_fallback=True,
    js_rendering_enabled=True
)
client = BrandScraperClient(config)

# Will try Playwright first, then Selenium if needed
result = await client.scrape_brand("https://complex-site.example.com")
```

### 4. Enhanced Error Handling and Logging

Comprehensive error handling with detailed logging helps identify and resolve extraction issues.

#### Capabilities

- **Detailed Error Messages**: Specific error types and messages for debugging
- **Retry Logic**: Configurable retry attempts with exponential backoff
- **Fallback Strategies**: Automatic fallback to static HTML when JS rendering fails
- **Error Logging**: Optional detailed logging of all extraction steps

#### Usage

```python
from automagik_tools.tools.brand_scraper import BrandScraperClient, BrandScraperConfig
import logging

# Enable detailed logging
logging.basicConfig(level=logging.INFO)

config = BrandScraperConfig(
    enable_detailed_logging=True,
    fallback_on_js_error=True,
    max_retries=3
)
client = BrandScraperClient(config)

result = await client.scrape_brand("https://problematic-site.example.com")

# Check for errors in specific extractors
if "error" in result.get("design_tokens", {}):
    print(f"Style extraction error: {result['design_tokens']['error']}")
```

## Configuration Options

### Complete Configuration Reference

```python
from automagik_tools.tools.brand_scraper import BrandScraperConfig

config = BrandScraperConfig(
    # Core settings
    timeout=30,                      # HTTP request timeout
    max_retries=3,                   # Number of retry attempts
    user_agent="...",                # Custom user agent
    
    # JavaScript Rendering
    enable_playwright=True,          # Enable Playwright for JS rendering
    selenium_fallback=False,         # Use Selenium as fallback
    js_rendering_enabled=True,       # Enable JS rendering
    js_rendering_timeout=30,         # Timeout for JS rendering
    
    # Tailwind Support
    use_tailwind_mapping=True,       # Enable Tailwind class mapping
    
    # Extraction Options
    extract_styles=True,             # Extract CSS and design tokens
    extract_images=True,             # Extract logos and images
    extract_tone=True,               # Analyze voice and tone
    
    # Limits
    max_images=20,                   # Max images to extract
    max_text_length=10000,           # Max text for tone analysis
    
    # Error Handling
    enable_detailed_logging=True,    # Enable detailed logs
    fallback_on_js_error=True,       # Fallback to static HTML on error
    
    # Convex Storage (optional)
    convex_url="https://...",        # Convex backend URL
    convex_api_key="..."             # Convex API key
)
```

### Environment Variables

All configuration options can be set via environment variables with the `BRAND_SCRAPER_` prefix:

```bash
export BRAND_SCRAPER_ENABLE_PLAYWRIGHT=true
export BRAND_SCRAPER_SELENIUM_FALLBACK=false
export BRAND_SCRAPER_USE_TAILWIND_MAPPING=true
export BRAND_SCRAPER_JS_RENDERING_TIMEOUT=30
export BRAND_SCRAPER_ENABLE_DETAILED_LOGGING=true
```

## Use Cases

### Scraping Tailwind-Heavy Sites

Perfect for modern websites built with Tailwind CSS:

```python
config = BrandScraperConfig(
    use_tailwind_mapping=True,
    js_rendering_enabled=True,
    extract_styles=True
)
client = BrandScraperClient(config)

# Extract from a Tailwind site
result = await client.scrape_brand("https://tailwind-site.example.com")

# Get Tailwind-specific design tokens
tailwind = result["tailwind"]
colors = tailwind["design_tokens"]["colors"]
```

### Scraping JavaScript SPAs

For React, Vue, Angular, and other JavaScript-heavy apps:

```python
config = BrandScraperConfig(
    enable_playwright=True,
    js_rendering_enabled=True,
    js_rendering_timeout=45  # Longer timeout for complex apps
)
client = BrandScraperClient(config)

result = await client.scrape_brand("https://react-app.example.com")
```

### Batch Processing with Fallbacks

Process multiple sites with automatic fallback handling:

```python
config = BrandScraperConfig(
    enable_playwright=True,
    selenium_fallback=True,
    fallback_on_js_error=True,
    enable_detailed_logging=True
)
client = BrandScraperClient(config)

urls = [
    "https://site1.example.com",
    "https://site2.example.com",
    "https://site3.example.com"
]

for url in urls:
    result = await client.scrape_brand(url)
    print(f"{url}: {result['status']} ({result.get('render_method')})")
```

## Troubleshooting

### Playwright Not Working

**Problem**: "Playwright is not available" error

**Solution**:
```bash
pip install playwright
playwright install chromium
```

### Selenium Not Working

**Problem**: "Selenium is not available" error

**Solution**:
```bash
pip install selenium
# ChromeDriver should be automatically managed by Selenium 4+
```

### JS Rendering Timeout

**Problem**: Sites timing out during rendering

**Solution**:
```python
config = BrandScraperConfig(
    js_rendering_timeout=60,  # Increase timeout
    fallback_on_js_error=True  # Enable fallback
)
```

### Missing Tailwind Classes

**Problem**: Not all Tailwind classes are detected

**Solution**: The parser uses pattern matching. Ensure classes follow standard Tailwind naming conventions. Custom classes may not be detected automatically.

## Performance Considerations

### Rendering Performance

- **Static HTML**: Fastest, but misses dynamic content (~1-2 seconds)
- **Playwright**: Slower but accurate (~5-10 seconds)
- **Selenium**: Similar to Playwright (~5-15 seconds)

### Best Practices

1. **Use JS rendering only when needed**: Set `js_rendering_enabled=False` for static sites
2. **Configure appropriate timeouts**: Balance between accuracy and speed
3. **Enable fallbacks**: Ensure `fallback_on_js_error=True` for production
4. **Batch processing**: Process multiple URLs in parallel when possible
5. **Cache results**: Store extracted data to avoid repeated scraping

## Testing

The enhanced features include comprehensive test coverage:

- Unit tests for Tailwind parser
- Unit tests for JavaScript renderers
- Integration tests with mock HTML
- Error handling tests

Run tests:
```bash
pytest tests/tools/test_brand_scraper.py tests/tools/test_brand_scraper_enhanced.py -v
```

## Support

For issues, questions, or feature requests:
- Check existing tests for usage examples
- Review error logs with `enable_detailed_logging=True`
- Consult the main Brand Scraper documentation
