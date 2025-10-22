# System Architecture Documentation

## 🏗️ Architecture Overview

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                         │
│                    (Command Line)                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                   DataPipeline (main.py)                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  • URL Reading                                       │   │
│  │  • Orchestration                                     │   │
│  │  • Error Handling                                    │   │
│  │  • Statistics Tracking                               │   │
│  └─────────────────────────────────────────────────────┘   │
└──────┬───────────────────┬───────────────────┬──────────────┘
       │                   │                   │
       ↓                   ↓                   ↓
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  WebScraper  │    │  Classifier  │    │ GitManager   │
│ (scraper.py) │    │(classifier.py)│   │(git_utils.py)│
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       ↓                   ↓                   ↓
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  BeautifulSoup│   │sentence-trans-│   │  GitPython   │
│  + requests   │   │  formers      │   │              │
└───────────────┘   └───────────────┘   └──────────────┘
```

## 📦 Component Design

### 1. DataPipeline (main.py)

**Responsibilities**:

- Read URLs from input file
- Coordinate scraping, classification, and storage
- Manage CSV metadata logging
- Trigger Git commits
- Track statistics

**Key Methods**:

```python
__init__(urls_file)          # Initialize pipeline
_setup_directories()         # Create folder structure
_read_urls()                 # Load URLs from file
process_url(url, page_id)    # Process single URL
_save_content(text, cat, name) # Save extracted text
_log_to_csv(metadata)        # Append to CSV
run()                        # Execute full pipeline
```

**Flow**:

1. Initialize components (scraper, classifier, git)
2. Create category directories
3. Read URLs from file
4. For each URL:
   - Scrape content
   - Classify category
   - Save to file
   - Commit file
   - Log to CSV
   - Commit CSV
5. Generate summary

### 2. WebScraper (scraper.py)

**Responsibilities**:

- Download HTML content
- Parse and extract clean text
- Remove navigation/headers/footers
- Detect duplicates via template comparison
- Quality filtering

**Key Methods**:

```python
__init__(template_url)       # Load template
download(url)                # Fetch HTML
_extract_text(html)          # Parse and clean
extract_content(html, url)   # Get text + metadata
compare_similarity(t1, t2)   # TF-IDF cosine similarity
is_duplicate(text)           # Check against template
is_quality_content(text)     # Validate quality
get_page_name(url)           # Generate filename
scrape(url)                  # Complete scrape workflow
```

**Text Extraction Pipeline**:

```
Raw HTML
    ↓
Remove <script>, <style>, <meta>
    ↓
Remove comments
    ↓
Remove nav, header, footer by selector
    ↓
Extract <p>, <h1>-<h6>, <li> tags
    ↓
Filter short snippets (<20 chars)
    ↓
Clean whitespace and newlines
    ↓
Clean Text
```

**Duplicate Detection**:

- TF-IDF vectorization (1000 features)
- Cosine similarity with template
- Threshold: 0.85 (85% similar = duplicate)

### 3. PageClassifier (classifier.py)

**Responsibilities**:

- Rule-based keyword matching
- Semantic similarity with embeddings
- Hybrid classification strategy
- Category information management

**Key Methods**:

```python
__init__(model_name)         # Initialize model
_load_model()                # Load sentence-transformers
_rule_based_classify(t, u)   # Keyword matching
_semantic_classify(t, u)     # Embedding similarity
classify(text, url, title)   # Hybrid classification
get_category_info(cat)       # Get category details
get_all_categories()         # List categories
```

**Classification Strategy**:

```
Input: Text + URL
    ↓
Rule-Based Classification
    │
    ├─ Keyword Match ≥ 20%? ─→ Return Category (confidence: 0.8)
    │
    └─ No confident match
         ↓
    Semantic Classification
         │
         ├─ Similarity ≥ 0.5? ─→ Return Category (confidence: 0.6)
         │
         └─ Below threshold ─→ Default: college_info (confidence: 0.3)
```

**Category Embeddings**:

- Precomputed on initialization
- Combines description + keywords
- Model: `all-MiniLM-L6-v2` (90MB)
- Dimension: 384

### 4. GitManager (git_utils.py)

**Responsibilities**:

- Initialize Git repository
- Stage and commit files
- Generate descriptive commit messages
- Provide repository status

**Key Methods**:

```python
__init__(repo_path)          # Open/init repo
_initialize_repo()           # Setup Git
commit_file(path, msg)       # Commit single file
commit_multiple(paths, msg)  # Commit batch
commit_metadata(csv, op)     # Commit CSV
get_status()                 # Repo info
```

**Commit Patterns**:

- Content: `"Added extracted text for '{title}' (Category: {cat})"`
- Metadata: `"Updated metadata: Added metadata for '{title}'"`
- Summary: `"Added pipeline execution summary"`

## 🔄 Data Flow

### Single URL Processing Flow

```
1. URL Input
   ↓
2. WebScraper.scrape(url)
   ├─ download(url) → HTML
   ├─ extract_content(html, url) → text, metadata
   ├─ is_quality_content(text) → bool
   └─ is_duplicate(text) → bool
   ↓
3. PageClassifier.classify(text, url, title)
   ├─ _rule_based_classify() → category | None
   └─ _semantic_classify() → category | None
   ↓
4. Save to file
   ├─ data/extracted/{category}/{page_name}.txt
   └─ GitManager.commit_file()
   ↓
5. Log to CSV
   ├─ data/data_inventory.csv
   └─ GitManager.commit_metadata()
   ↓
6. Return success/failure
```

### Configuration Loading

```
config.py (defaults)
    ↓
Environment Variables (.env) [optional]
    ↓
Runtime Parameters [optional]
    ↓
Final Configuration
```

## 🎨 Design Patterns

### 1. Strategy Pattern

- **Used in**: Classifier
- **Purpose**: Switch between rule-based and semantic strategies
- **Benefit**: Easy to add new classification methods

### 2. Template Method Pattern

- **Used in**: DataPipeline.process_url()
- **Purpose**: Define processing skeleton with customizable steps
- **Benefit**: Consistent workflow with flexible implementation

### 3. Facade Pattern

- **Used in**: DataPipeline
- **Purpose**: Provide simple interface to complex subsystems
- **Benefit**: Easy to use, hides complexity

### 4. Singleton Pattern (Implicit)

- **Used in**: SentenceTransformer model loading
- **Purpose**: Load model once, reuse for all classifications
- **Benefit**: Memory efficiency, faster processing

## 🔧 Configuration System

### Centralized Configuration (config.py)

```python
# URLs and Templates
TEMPLATE_URL = "..."
SITEMAP_INDEX = "..."

# Thresholds
TEMPLATE_DUPLICATE_THRESHOLD = 0.85
SEMANTIC_SIMILARITY_THRESHOLD = 0.5
CONTENT_FILTER = {min_text_length, min_paragraphs, min_sentences}

# Categories
CATEGORIES = {
    "category_name": {
        "tag": "...",
        "description": "...",
        "keywords": [...]
    }
}

# Paths
DATA_DIR, EXTRACTED_DATA_DIR, CSV_LOG_FILE

# Git Settings
GIT_ENABLE, GIT_AUTO_COMMIT
```

**Override Hierarchy**:

1. Hardcoded defaults (config.py)
2. Environment variables (.env)
3. Command-line arguments (future)

## 📊 Data Models

### Scraped Data Dictionary

```python
{
    "url": str,              # Source URL
    "title": str,            # Page title
    "text": str,             # Extracted clean text
    "page_name": str,        # Generated filename
    "metadata": {
        "title": str,
        "url": str,
        "text_length": int,
        "paragraphs": int,
        "headings": int,
        "word_count": int
    }
}
```

### CSV Schema

```csv
id: int                    # Sequential page ID
title: str                 # Page title
source_url: str            # Original URL
category: str              # Classification category
tag: str                   # Category tag
source_file: str           # Relative path to text file
tags: str                  # Comma-separated keywords
word_count: int            # Number of words
confidence: float          # Classification confidence (0.0-1.0)
```

### Git Commit Structure

```
Hash: abc1234
Author: System
Date: 2024-10-20 10:30:45
Message: "Added extracted text for 'About SDIT' (Category: college_info)"

Changes:
  A  data/extracted/college_info/about.txt
```

## 🔐 Error Handling Strategy

### Defensive Programming

- All network calls wrapped in try-except
- Graceful degradation (e.g., Git disabled if not installed)
- Input validation on URLs, text, paths
- Logging at multiple levels (DEBUG, INFO, WARNING, ERROR)

### Error Recovery

```python
try:
    result = process_url(url)
except NetworkError:
    log.warning("Network timeout, skipping")
    stats["failed"] += 1
except ParseError:
    log.error("HTML parse error, skipping")
    stats["failed"] += 1
except Exception as e:
    log.error(f"Unexpected error: {e}")
    stats["failed"] += 1
    continue  # Don't crash pipeline
```

## 📈 Performance Optimization

### Current Performance

- Single URL: 5-10 seconds (network + classification)
- Batch (100 URLs): 8-15 minutes
- Full dataset (3564 URLs): ~7 hours

### Optimization Opportunities

1. **Parallel Processing**:

   ```python
   from concurrent.futures import ThreadPoolExecutor

   with ThreadPoolExecutor(max_workers=5) as executor:
       executor.map(process_url, urls)
   ```

   Expected: 5x speedup → 1.5 hours

2. **Model Caching**:

   - Already implemented (singleton model loading)
   - Saves 2-3 seconds per classification

3. **Batch Classification**:

   ```python
   # Instead of: model.encode(text1), model.encode(text2)
   # Use: model.encode([text1, text2])
   ```

   Expected: 30% faster classification

4. **Request Pooling**:
   ```python
   session = requests.Session()
   session.mount('http://', HTTPAdapter(pool_connections=10))
   ```
   Expected: 10-20% faster downloads

## 🧪 Testing Strategy

### Unit Tests (Future)

```python
test_scraper.py:
  - test_download_success()
  - test_extract_text_removes_nav()
  - test_duplicate_detection()
  - test_quality_filter()

test_classifier.py:
  - test_rule_based_classification()
  - test_semantic_classification()
  - test_fallback_mechanism()

test_git_utils.py:
  - test_init_repo()
  - test_commit_file()
  - test_status()
```

### Integration Tests

```python
test_pipeline.py:
  - test_end_to_end_processing()
  - test_error_recovery()
  - test_csv_logging()
```

### Manual Testing

- Run `test_setup.py` for component validation
- Process 3 sample URLs with mini pipeline
- Verify Git commits and CSV entries

## 🔮 Extensibility Points

### Adding New Categories

1. Edit `src/config.py` → `CATEGORIES`
2. Add entry with tag, description, keywords
3. Re-run pipeline (directory auto-created)

### Custom Classification Logic

1. Subclass `PageClassifier`
2. Override `_rule_based_classify()` or `_semantic_classify()`
3. Inject into `DataPipeline.__init__(classifier=CustomClassifier())`

### Alternative Storage

1. Implement `StorageBackend` interface
2. Replace `_save_content()` in DataPipeline
3. Examples: S3, Database, Cloud Storage

### Webhook Integration

```python
# In DataPipeline.process_url(), after save:
requests.post(WEBHOOK_URL, json={
    "event": "page_processed",
    "url": url,
    "category": category
})
```

## 📚 Dependencies Graph

```
main.py
  ├─ scraper.py
  │   ├─ requests
  │   ├─ beautifulsoup4
  │   ├─ lxml
  │   └─ scikit-learn
  ├─ classifier.py
  │   ├─ sentence-transformers
  │   ├─ torch
  │   └─ scikit-learn
  ├─ git_utils.py
  │   └─ gitpython
  ├─ config.py
  └─ pandas
```

## 🎯 Design Principles Applied

✅ **Separation of Concerns**: Each module has single responsibility
✅ **DRY**: Configuration centralized, no code duplication
✅ **SOLID**: Open for extension, closed for modification
✅ **Type Hints**: All public methods typed
✅ **Documentation**: Comprehensive docstrings
✅ **Logging**: Structured, leveled logging throughout
✅ **Error Handling**: Defensive programming with graceful degradation

---

**Last Updated**: October 20, 2025
**Version**: 1.0.0
**Maintainer**: AI Development Team
