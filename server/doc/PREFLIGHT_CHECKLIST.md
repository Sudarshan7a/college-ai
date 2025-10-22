# Pre-Flight Checklist

Before running the full pipeline, verify all items below:

## ✅ Installation Verification

- [ ] Python 3.10+ installed (`python --version`)
- [ ] Virtual environment created (recommended)
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] No import errors (`python -c "from src.main import DataPipeline; print('OK')"`)

## ✅ File Structure

- [ ] `allUrls.txt` exists with valid URLs
- [ ] `src/` directory contains all modules:
  - [ ] `main.py`
  - [ ] `scraper.py`
  - [ ] `classifier.py`
  - [ ] `git_utils.py`
  - [ ] `config.py`
- [ ] `data/` directory exists (or will be auto-created)
- [ ] Documentation files present:
  - [ ] `README.md`
  - [ ] `QUICKSTART.md`
  - [ ] `ARCHITECTURE.md`
  - [ ] `PROJECT_SUMMARY.md`

## ✅ Configuration

- [ ] Review `src/config.py` settings:
  - [ ] `TEMPLATE_URL` is correct
  - [ ] `TEMPLATE_DUPLICATE_THRESHOLD` = 0.85 (adjust if needed)
  - [ ] `SEMANTIC_SIMILARITY_THRESHOLD` = 0.5 (adjust if needed)
  - [ ] `CONTENT_FILTER` values appropriate for your content
- [ ] Git settings:
  - [ ] `GIT_ENABLE = True` (or False if you don't want Git)
  - [ ] `GIT_AUTO_COMMIT = True`

## ✅ Environment

- [ ] Internet connection active (for web scraping)
- [ ] Sufficient disk space (~10MB for 3500 pages)
- [ ] Sufficient RAM (~2GB for sentence-transformers model)

## ✅ Testing (Recommended)

- [ ] Run `python test_setup.py` successfully
- [ ] All component tests pass
- [ ] Mini pipeline (3 URLs) works correctly

## ✅ Ready to Run

Once all items checked, you can run:

### Option 1: Test with Sample URLs

```powershell
# Edit allUrls.txt to keep only first 10 URLs for testing
python -m src.main
```

### Option 2: Full Pipeline

```powershell
# Process all URLs in allUrls.txt
python -m src.main
```

Expected time: 3564 URLs × 7 seconds ≈ 7 hours

### Option 3: Monitor Progress

```powershell
# Watch the log file in another terminal
Get-Content scraping.log -Wait -Tail 20
```

## 📊 Success Indicators

During execution, you should see:

✅ `INFO - Scraping: https://...`
✅ `INFO - Successfully scraped: ... chars, ... words`
✅ `INFO - Classified as: <category> (confidence: ...)`
✅ `INFO - Saved content to: data/extracted/<category>/<file>.txt`
✅ `INFO - Committed: Added extracted text for '...'`
✅ `INFO - ✓ Successfully processed [N]: <url>`

## ⚠️ Warning Signs

Watch for these messages:

⚠️ `WARNING - Failed to download <url>` → Network issue or invalid URL
⚠️ `WARNING - Content quality check failed` → Page has too little content
⚠️ `WARNING - Duplicate/boilerplate detected` → Page similar to template
⚠️ `ERROR - Error processing <url>: ...` → Unexpected error (see logs)

## 🔍 Verification After Run

- [ ] Check `data/extracted/` directories contain .txt files
- [ ] Verify `data/data_inventory.csv` has entries
- [ ] Confirm Git commits: `git log --oneline`
- [ ] Review `PIPELINE_SUMMARY.txt` for statistics
- [ ] Check `scraping.log` for any errors

## 📈 Expected Output Structure

```
data/
├── data_inventory.csv           ← Metadata log
├── extracted/
│   ├── college_info/           ← ~20-30% of pages
│   ├── departments/            ← ~15-20% of pages
│   ├── admissions/             ← ~10-15% of pages
│   ├── placements/             ← ~10-15% of pages
│   ├── events/                 ← ~10-15% of pages
│   ├── facilities/             ← ~5-10% of pages
│   ├── assistance/             ← ~5-10% of pages
│   └── admin_data/             ← ~5-10% of pages
└── raw_pages/                  ← From data_fetcher (if used)
```

## 🚨 Emergency Stop

If you need to stop the pipeline:

1. Press `Ctrl+C` in terminal
2. Pipeline will stop gracefully
3. Already processed pages are saved and committed
4. To resume: Comment out processed URLs in `allUrls.txt` and restart

## 📞 Help Resources

- **Installation issues**: See QUICKSTART.md
- **Configuration help**: See README.md
- **Architecture questions**: See ARCHITECTURE.md
- **Git confusion**: See GIT_COMMITS_EXAMPLES.md
- **General overview**: See PROJECT_SUMMARY.md

## ✨ Final Checklist

- [ ] All pre-flight items checked
- [ ] Test run successful
- [ ] Disk space available
- [ ] Ready to start full pipeline

**Status**: ⬜ NOT READY ✅ READY TO GO

---

**Good luck with your extraction! 🚀**

_Tip: Start with a small subset (10-20 URLs) to verify everything works before processing all 3564 URLs._
