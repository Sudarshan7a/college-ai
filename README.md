# College Website Data Extraction Pipeline

A production-grade Python system for automated web scraping, content extraction, intelligent categorization, and Git-based version control.

## 🎯 Overview

This pipeline extracts meaningful content from college website URLs, classifies pages into 8 predefined categories using hybrid ML techniques, and maintains incremental Git commits for complete auditability.

### Key Features

- **Smart Web Scraping**: Downloads HTML, removes navigation/headers/footers, extracts clean body text
- **Duplicate Detection**: Compares against template pages to reject boilerplate (TF-IDF similarity)
- **Hybrid Classification**: Rule-based keyword matching + semantic embeddings (sentence-transformers)
- **Structured Storage**: Saves content in category-based folders with metadata logging
- **Incremental Git Commits**: Commits after each operation for rollback capability
- **Quality Filtering**: Validates content length, paragraph count, and text quality

## 📁 Project Structure

```
college-ai/
├── allUrls.txt                  # Input: URLs to process (one per line)
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── scraping.log                 # Runtime logs
├── PIPELINE_SUMMARY.txt         # Execution summary
│
├── data/
│   ├── data_inventory.csv       # Metadata log (id, title, url, category, etc.)
│   ├── raw_pages/               # Original scraped pages (if data_fetcher used)
│   └── extracted/               # Categorized extracted content
│       ├── college_info/        # About, Vision, Mission
│       ├── departments/         # CSE, ECE, Mechanical, etc.
│       ├── admissions/          # Eligibility, Fees, Calendar
│       ├── placements/          # Recruiters, Stats, Training
│       ├── events/              # Fests, Workshops, Clubs
│       ├── facilities/          # Campus, Library, Hostel
│       ├── assistance/          # FAQs, Contact, Helpdesk
│       └── admin_data/          # Timetables, NAAC, Reports
│
├── src/
│   ├── __init__.py
│   ├── config.py                # Configuration and category schema
│   ├── scraper.py               # WebScraper class
│   ├── classifier.py            # PageClassifier (hybrid)
│   ├── git_utils.py             # GitManager for version control
│   ├── main.py                  # DataPipeline orchestration
│   └── data_fetcher.py          # (Optional) URL collection from sitemaps
│
└── notebooks/                   # Jupyter notebooks for analysis
```

## 🚀 Installation

### Prerequisites

- Python 3.10 or higher
- Git installed and configured
- 4GB+ RAM (for sentence-transformers model)

### Setup

1. **Clone or navigate to repository**:

   ```bash
   cd "c:\Users\Sudupa\Documents\coding\projects\college ai"
   ```

2. **Create virtual environment** (recommended):

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**:

   ```powershell
   pip install -r requirements.txt
   ```

   This installs:

   - `requests`, `beautifulsoup4`, `lxml` - Web scraping
   - `sentence-transformers` - Semantic embeddings
   - `scikit-learn` - TF-IDF, cosine similarity
   - `pandas` - CSV/data handling
   - `gitpython` - Automated Git operations
   - `torch`, `transformers` - Deep learning backend

4. **Prepare URLs file**:

   - Edit `allUrls.txt` and add URLs (one per line)
   - Comments start with `#`

   Example:

   ```
   https://sdit.ac.in/about/
   https://sdit.ac.in/departments/cse/
   https://sdit.ac.in/admissions/
   # https://sdit.ac.in/old-page/  (commented out)
   ```

## 🎮 Usage

### Basic Execution

Run the complete pipeline:

```powershell
python -m src.main
```

### What Happens

1. **Initialization**:

   - Creates category directories under `data/extracted/`
   - Initializes `data_inventory.csv` with headers
   - Loads template page for duplicate detection
   - Initializes Git repository (if not exists)

2. **Processing Loop** (for each URL):

   - Downloads HTML
   - Extracts clean text (removes nav/header/footer)
   - Checks quality (min length, paragraphs, sentences)
   - Compares against template (rejects if >85% similar)
   - Classifies into category (rule-based → semantic fallback)
   - Saves to `data/extracted/<category>/<page_name>.txt`
   - Commits file: `"Added extracted text for 'Page Title' (Category: X)"`
   - Logs to CSV
   - Commits CSV: `"Added metadata for 'Page Title'"`

3. **Completion**:
   - Prints statistics summary
   - Generates `PIPELINE_SUMMARY.txt`
   - Final commit: `"Added pipeline execution summary"`

### Output

**Console Logs**:

```
============================================================
Processing [1]: https://sdit.ac.in/about/
============================================================
INFO - Scraping: https://sdit.ac.in/about/
INFO - Successfully scraped: 2456 chars, 389 words
INFO - Classifying: https://sdit.ac.in/about/
INFO - Rule-based classification: college_info (score: 0.35)
INFO - Classified as: college_info (tag: college_info, confidence: 0.80)
INFO - Saved content to: data\extracted\college_info\about.txt
INFO - Committed: Added extracted text for 'About SDIT' (Category: college_info)
INFO - Committed: Updated metadata: Added metadata for 'About SDIT'
INFO - ✓ Successfully processed [1]: https://sdit.ac.in/about/
```

**CSV Log** (`data/data_inventory.csv`):

```csv
id,title,source_url,category,tag,source_file,tags,word_count,confidence
1,About SDIT,https://sdit.ac.in/about/,college_info,college_info,data\extracted\college_info\about.txt,"about, vision, mission, administration, principal",389,0.80
```

## ⚙️ Configuration

Edit `src/config.py` to customize:

### Template Page

```python
TEMPLATE_URL = "https://sdit.ac.in/rakshitha-b-k-3/"  # Boilerplate example
TEMPLATE_DUPLICATE_THRESHOLD = 0.85  # 85% similarity = duplicate
```

### Quality Filters

```python
CONTENT_FILTER = {
    'min_text_length': 500,    # Minimum characters
    'min_paragraphs': 3,       # Minimum <p> tags
    'min_sentences': 5         # Minimum sentences
}
```

### Classification Thresholds

```python
SEMANTIC_SIMILARITY_THRESHOLD = 0.5  # Minimum for semantic match
```

### Git Settings

```python
GIT_ENABLE = True           # Enable Git operations
GIT_AUTO_COMMIT = True      # Auto-commit after each step
```

## 🏷️ Category Schema

| Category         | Tag          | Keywords (examples)                                     |
| ---------------- | ------------ | ------------------------------------------------------- |
| **College Info** | college_info | about, vision, mission, principal, administration       |
| **Departments**  | departments  | cse, ece, mechanical, faculty, curriculum               |
| **Admissions**   | admissions   | eligibility, application, fees, calendar, entrance      |
| **Placements**   | placements   | recruiter, career, training, job, stats, package        |
| **Events**       | events       | fest, workshop, nss, ieee, club, hackathon              |
| **Facilities**   | facilities   | campus, library, hostel, transport, lab, infrastructure |
| **Assistance**   | assistance   | faq, contact, helpdesk, grievance, support              |
| **Admin Data**   | admin_data   | timetable, naac, ssr, policy, accreditation             |

## 🔧 Advanced Usage

### Adding New Categories

1. Edit `src/config.py`:

   ```python
   CATEGORIES = {
       # ... existing categories ...
       "research": {
           "tag": "research",
           "description": "Research papers, projects, publications",
           "keywords": ["research", "paper", "publication", "project", "patent"]
       }
   }
   ```

2. Re-run pipeline - directory auto-created

### Custom Scraper Rules

Modify `src/scraper.py` → `_extract_text()` to handle site-specific structures:

```python
# Remove custom elements
for selector in soup.find_all("div", class_="advertisement"):
    selector.decompose()
```

### Parallel Processing

For large URL lists, modify `src/main.py`:

```python
from concurrent.futures import ThreadPoolExecutor

def run(self):
    urls = self._read_urls()

    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(lambda url: self.process_url(url, urls.index(url)+1), urls)
```

⚠️ **Warning**: Parallel requests may trigger rate limiting

## 📊 Metadata Schema

CSV columns in `data/data_inventory.csv`:

| Column      | Description                         | Example                               |
| ----------- | ----------------------------------- | ------------------------------------- |
| id          | Sequential page ID                  | 1, 2, 3...                            |
| title       | Page title                          | "About SDIT"                          |
| source_url  | Original URL                        | https://sdit.ac.in/about/             |
| category    | Classification category             | college_info                          |
| tag         | Category tag                        | college_info                          |
| source_file | Relative path to saved text         | data/extracted/college_info/about.txt |
| tags        | Comma-separated keywords            | "about, vision, mission"              |
| word_count  | Number of words extracted           | 389                                   |
| confidence  | Classification confidence (0.0-1.0) | 0.80                                  |

## 🧪 Testing & Validation

### Verify Installation

```powershell
python -c "from src.scraper import WebScraper; from src.classifier import PageClassifier; print('✓ All imports successful')"
```

### Test Single URL

```python
from src.main import DataPipeline

pipeline = DataPipeline()
pipeline.process_url("https://sdit.ac.in/about/", page_id=1)
```

### Check Git History

```powershell
git log --oneline --graph
```

Expected output:

```
* abc1234 Added pipeline execution summary
* def5678 Added metadata for 'About SDIT'
* ghi9012 Added extracted text for 'About SDIT' (Category: college_info)
```

## 🚨 Troubleshooting

### Import Errors

```
ImportError: No module named 'sentence_transformers'
```

**Solution**: Install dependencies

```powershell
pip install sentence-transformers
```

### Connection Timeout

```
Error downloading https://...: Timeout
```

**Solution**: Increase timeout in `src/config.py`:

```python
REQUEST_TIMEOUT = 30  # seconds
```

### Git Not Initialized

```
Warning: GitPython not installed. Git operations disabled.
```

**Solution**: Install GitPython

```powershell
pip install gitpython
```

### Template Page Not Loading

```
WARNING - Failed to load template page
```

**Solution**: Check `TEMPLATE_URL` in config.py or set to `None` to disable duplicate detection

### Low Quality Content Skipped

```
WARNING - Content quality check failed
```

**Solution**: Lower thresholds in `CONTENT_FILTER` (config.py)

## 🎯 Evaluation Criteria

| Criterion           | Weight | Implementation                                        |
| ------------------- | ------ | ----------------------------------------------------- |
| **Accuracy**        | 30%    | Hybrid classifier (rule-based + semantic)             |
| **Code Quality**    | 25%    | Modular, typed, documented, PEP8 compliant            |
| **Robustness**      | 20%    | Exception handling, quality filters, logging          |
| **Automation**      | 15%    | Incremental Git commits, metadata tracking            |
| **Maintainability** | 10%    | Config-driven, extensible categories, clear structure |

## 🔮 Future Improvements

### Phase 2 Enhancements

- [ ] **Parallel Scraping**: ThreadPoolExecutor with rate limiting
- [ ] **Database Storage**: SQLite/PostgreSQL instead of CSV
- [ ] **RAG Integration**: Vector database (Pinecone, Weaviate) for semantic search
- [ ] **API Endpoint**: FastAPI service for on-demand classification
- [ ] **Multi-language**: Support regional language content
- [ ] **Image Extraction**: Download and categorize images
- [ ] **PDF Parsing**: Extract text from PDF links
- [ ] **Scheduling**: Cron jobs for periodic re-scraping
- [ ] **Diff Detection**: Re-scrape only changed pages
- [ ] **Dashboard**: Streamlit/Gradio UI for monitoring

### RAG Ingestion Example

```python
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings

# After extraction, create vector store
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
texts = [Path(f).read_text() for f in Path("data/extracted").rglob("*.txt")]
vector_store = FAISS.from_texts(texts, embeddings)
vector_store.save_local("data/vector_db")
```

## 📜 License

MIT License - Free for academic and commercial use

## 👥 Contributors

- **Claude 4.5** - AI Code Generator & Data Engineer
- **Sudupa** - Project Lead

## 📞 Support

For issues or questions:

1. Check troubleshooting section above
2. Review `scraping.log` for detailed errors
3. Inspect Git history: `git log`
4. Check CSV for processed pages: `data/data_inventory.csv`

## 🙏 Acknowledgments

- **sentence-transformers**: Semantic text embeddings
- **BeautifulSoup**: HTML parsing excellence
- **scikit-learn**: Machine learning utilities
- **GitPython**: Programmatic Git control

---

**Built with ❤️ for automated knowledge extraction**
