# College AI - Web Data Fetcher

Python tool for scraping websites with intelligent content filtering. Automatically skips empty pages, student profiles, and other template-based content.

## Quick Start

```powershell
# 1. Activate environment
venv\Scripts\Activate.ps1

# 2. Extract all URLs from sitemaps
python extract_urls.py

# 3. Test a URL
python check_url.py "https://sdit.ac.in/sports/"

# 4. Run full crawl
python fetch_example.py
```

## Project Structure

```
├── src/
│   ├── data_fetcher.py    # Main scraping module
│   └── config.py          # Settings & configuration
├── data/raw_pages/        # Scraped content (auto-created)
├── extract_urls.py        # Extract all URLs from sitemaps
├── check_url.py           # Quick URL tester
├── test_fetcher.py        # Detailed analysis tool
├── fetch_example.py       # Full crawler example
└── requirements.txt
```

## Extract All URLs

Get all available URLs from the XML sitemaps:

```powershell
python extract_urls.py
```

**Output:**

```
Processing 7 sitemaps...
✓ post-sitemap.xml          1001 URLs
✓ post-sitemap2.xml         1000 URLs
✓ post-sitemap3.xml         1000 URLs
✓ post-sitemap4.xml          422 URLs
✓ page-sitemap.xml            48 URLs
✓ category-sitemap.xml        92 URLs
✓ author-sitemap.xml           2 URLs

✅ Saved 3564 unique URLs to: urls.txt
```

## Validate URLs

Check which URLs are valid (not templates) and save only meaningful ones:

```powershell
python validate_urls.py
```

**What it does:**

1. Fetches each URL and extracts content
2. Checks template similarity (skips student profiles, etc.)
3. Validates content (length, paragraphs, sentences)
4. Saves valid URLs to `valid_urls.txt`
5. Saves rejected URLs to `valid_urls_rejected.txt` for review

**Output:**

```
Validating 3564 URLs...
Progress: 50/3564 (1%) - Valid: 32 - Rate: 2.5 URLs/sec - ETA: 23.4 min
...
✅ Valid URLs:    1250 (35%)
❌ Rejected:      2314 (65%)
  • Template similarity: 1800 URLs
  • Text too short:        350 URLs
  • Not enough paragraphs:  164 URLs

📄 Valid URLs saved to: valid_urls.txt
```

**Custom files:**

```powershell
python validate_urls.py my_urls.txt my_valid_urls.txt
```

## How It Works

**Smart Filtering:**

1. Compares pages to template (empty student profile)
2. Skips pages with >70% similarity (other student profiles)
3. Validates content (length, paragraphs, sentences)
4. Saves only meaningful pages

**What Gets Saved:** ✅

- Articles with substantial content
- Pages with unique information
- Department/course pages

**What Gets Skipped:** ❌

- Student profile templates (~78% similar)
- Pages with <500 characters
- Pages with <3 paragraphs or <5 sentences

## Testing URLs

### Quick Check

```powershell
# Single URL
python check_url.py "https://sdit.ac.in/sports/"

# Compare multiple
python check_url.py compare "URL1" "URL2" "URL3"
```

**Output:**

```
✅ WILL BE SAVED
Reason: Content is meaningful
Details:
  • Text length: 2847 chars
  • Paragraphs: 8
  • Sentences: 12
  • Template similarity: 18.5%
```

### Detailed Analysis

```powershell
python test_fetcher.py test "https://sdit.ac.in/sports/"
```

Shows step-by-step: fetch → extract → template check → content validation → decision

## Running the Crawler

```powershell
python fetch_example.py
```

**Output:**

```
Starting data collection from sitemaps...
Processing 125 URLs...
✓ Saved 87 meaningful pages
✗ Skipped 32 similar/empty pages
✗ 6 errors/timeouts
Success rate: 93.6%
```

Files saved to: `data/raw_pages/page_XXXX_domain_path.txt`

## Configuration

Edit `src/config.py`:

```python
# Template URL (empty page to compare against)
TEMPLATE_URL = "https://sdit.ac.in/rakshitha-b-k-3/"

# Similarity threshold (0.0-1.0)
TEMPLATE_SIMILARITY_THRESHOLD = 0.7  # 70%

# Content requirements
CONTENT_FILTER = {
    'min_text_length': 500,    # characters
    'min_paragraphs': 3,       # <p> tags
    'min_sentences': 5         # sentence count
}

# Sitemaps to crawl
SITEMAPS = [
    "https://sdit.ac.in/post-sitemap.xml",
    "https://sdit.ac.in/page-sitemap.xml",
    # ... 5 more
]
```

## Customization

### More Aggressive Filtering

```python
TEMPLATE_SIMILARITY_THRESHOLD = 0.6  # Skip more similar pages
```

### Less Strict Content Filter

```python
CONTENT_FILTER = {
    'min_text_length': 300,
    'min_paragraphs': 2,
    'min_sentences': 3
}
```

### Specific Sitemaps Only

```python
# In fetch_example.py
sitemaps = ["https://sdit.ac.in/post-sitemap.xml"]  # Just posts
```

## Advanced Usage

### Programmatic Use

```python
from src.data_fetcher import DataFetcher

fetcher = DataFetcher(
    template_url="https://sdit.ac.in/rakshitha-b-k-3/",
    similarity_threshold=0.7,
    timeout=10
)

# From sitemaps
stats = fetcher.fetch_from_sitemaps([
    "https://sdit.ac.in/post-sitemap.xml"
])

# From URL list
stats = fetcher.fetch_urls([
    "https://sdit.ac.in/page1",
    "https://sdit.ac.in/page2"
])

print(f"Saved: {stats['meaningful_pages']}")
print(f"Skipped: {stats['empty_pages']}")
```

### Batch Testing

```powershell
python test_fetcher.py batch "URL1" "URL2" "URL3"
```

### Interactive Mode

```powershell
python test_fetcher.py
# Then enter URLs one at a time
```

## Troubleshooting

**Too many pages skipped?**

- Lower threshold: `TEMPLATE_SIMILARITY_THRESHOLD = 0.8`
- Reduce content requirements in `CONTENT_FILTER`

**Not enough filtering?**

- Raise threshold: `TEMPLATE_SIMILARITY_THRESHOLD = 0.6`
- Check template URL is correct

**Connection timeouts?**

- Increase timeout in `fetch_example.py`: `timeout=20`

**Module not found?**

```powershell
pip install -r requirements.txt
```

## Requirements

- Python 3.12+
- requests, beautifulsoup4, lxml

## Target Website

- **Sitemap**: https://sdit.ac.in/sitemap_index.xml
- **Template**: https://sdit.ac.in/rakshitha-b-k-3/

## License

Educational project
