"""
Configuration file for data fetching operations.

Customize sitemaps, filters, and output settings here.
"""

# Sitemap Index URL (automatically extracts all sitemaps)
SITEMAP_INDEX = "https://sdit.ac.in/sitemap_index.xml"

# Individual Sitemap URLs to crawl
SITEMAPS = [
    "https://sdit.ac.in/post-sitemap.xml",
    "https://sdit.ac.in/post-sitemap2.xml",
    "https://sdit.ac.in/post-sitemap3.xml",
    "https://sdit.ac.in/post-sitemap4.xml",
    "https://sdit.ac.in/page-sitemap.xml",
    "https://sdit.ac.in/category-sitemap.xml",
    "https://sdit.ac.in/author-sitemap.xml"
]

# Empty template page URL for filtering similar pages
# Pages with content structure/text similar to this page will be skipped
TEMPLATE_URL = "https://sdit.ac.in/rakshitha-b-k-3/"

# Content filtering thresholds
CONTENT_FILTER = {
    'min_text_length': 500,      # Minimum characters
    'min_paragraphs': 3,         # Minimum <p> tags
    'min_sentences': 5           # Minimum sentences
}

# Template similarity threshold (0.0-1.0)
# 0.7 means if 70% of words are common with empty template, skip the page
TEMPLATE_SIMILARITY_THRESHOLD = 0.7

# Output settings
OUTPUT_DIR = "data/raw_pages"

# Request settings
REQUEST_TIMEOUT = 10  # seconds
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Logging level
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
