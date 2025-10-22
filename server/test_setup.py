"""
Test script to validate the setup and run a small test extraction.

This script tests each component individually before running the full pipeline.
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_imports():
    """Test that all required packages are installed."""
    logger.info("Testing imports...")
    
    try:
        import requests
        logger.info("✓ requests")
    except ImportError:
        logger.error("✗ requests not installed")
        return False
    
    try:
        from bs4 import BeautifulSoup
        logger.info("✓ beautifulsoup4")
    except ImportError:
        logger.error("✗ beautifulsoup4 not installed")
        return False
    
    try:
        import sklearn
        logger.info("✓ scikit-learn")
    except ImportError:
        logger.error("✗ scikit-learn not installed")
        return False
    
    try:
        import pandas
        logger.info("✓ pandas")
    except ImportError:
        logger.error("✗ pandas not installed")
        return False
    
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("✓ sentence-transformers")
    except ImportError:
        logger.error("✗ sentence-transformers not installed")
        logger.error("  Install with: pip install sentence-transformers")
        return False
    
    logger.info("All critical imports successful!\n")
    return True


def test_scraper():
    """Test the scraper module."""
    logger.info("Testing scraper...")
    
    try:
        from src.scraper import WebScraper
        
        scraper = WebScraper()
        logger.info("✓ WebScraper initialized")
        
        # Test with a simple URL
        test_url = "https://sdit.ac.in/about/"
        logger.info(f"Testing scrape on: {test_url}")
        
        result = scraper.scrape(test_url)
        
        if result:
            logger.info(f"✓ Scrape successful:")
            logger.info(f"  Title: {result['title'][:50]}...")
            logger.info(f"  Words: {result['metadata']['word_count']}")
            logger.info(f"  Page name: {result['page_name']}")
        else:
            logger.warning("⚠ Scrape returned None (may be duplicate or low quality)")
        
        logger.info("Scraper test complete!\n")
        return True
        
    except Exception as e:
        logger.error(f"✗ Scraper test failed: {e}")
        return False


def test_classifier():
    """Test the classifier module."""
    logger.info("Testing classifier...")
    
    try:
        from src.classifier import PageClassifier
        
        classifier = PageClassifier()
        logger.info("✓ PageClassifier initialized")
        
        # Test classification
        test_text = "The Computer Science department offers programs in CSE and IT with experienced faculty."
        test_url = "https://sdit.ac.in/departments/cse/"
        
        logger.info("Testing classification...")
        category, tag, confidence = classifier.classify(test_text, test_url)
        
        logger.info(f"✓ Classification successful:")
        logger.info(f"  Category: {category}")
        logger.info(f"  Tag: {tag}")
        logger.info(f"  Confidence: {confidence:.2f}")
        
        # List all categories
        categories = classifier.get_all_categories()
        logger.info(f"\n  Available categories: {', '.join(categories)}")
        
        logger.info("Classifier test complete!\n")
        return True
        
    except Exception as e:
        logger.error(f"✗ Classifier test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_mini_pipeline():
    """Run a mini pipeline on 3 URLs."""
    logger.info("Running mini pipeline test (3 URLs)...")
    
    try:
        from src.main import DataPipeline
        
        # Check for test_urls.txt first, then fall back to allUrls.txt
        urls_file = Path("test_urls.txt")
        if urls_file.exists():
            logger.info("Using test_urls.txt for testing")
        else:
            urls_file = Path("allUrls.txt")
            logger.info("Using allUrls.txt (test_urls.txt not found)")
        
        if not urls_file.exists():
            logger.error("✗ No URLs file found (tried test_urls.txt and allUrls.txt)")
            return False
        
        urls = []
        with open(urls_file, 'r', encoding='utf-8-sig') as f:
            for line in f:
                url = line.strip()
                if url and not url.startswith('#'):
                    urls.append(url)
                if len(urls) >= 3:
                    break
        
        logger.info(f"Testing with {len(urls)} URLs:")
        for i, url in enumerate(urls, 1):
            logger.info(f"  {i}. {url}")
        
        # Create pipeline
        pipeline = DataPipeline()
        
        # Process each URL
        for idx, url in enumerate(urls, 1):
            logger.info(f"\n--- Processing URL {idx} ---")
            success = pipeline.process_url(url, idx)
            
            if success:
                logger.info(f"✓ URL {idx} processed successfully")
            else:
                logger.warning(f"⚠ URL {idx} failed or skipped")
        
        # Print stats
        logger.info("\n" + "="*60)
        logger.info("Mini Pipeline Stats:")
        logger.info(f"  Scraped: {pipeline.stats['scraped']}/{len(urls)}")
        logger.info(f"  Classified: {pipeline.stats['classified']}/{len(urls)}")
        logger.info(f"  Saved: {pipeline.stats['saved']}/{len(urls)}")
        logger.info("="*60)
        
        logger.info("\n✓ Mini pipeline test complete!\n")
        return True
        
    except Exception as e:
        logger.error(f"✗ Mini pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("SETUP VALIDATION TEST")
    print("="*60)
    print()
    
    tests = [
        ("Import Test", test_imports),
        ("Scraper Test", test_scraper),
        ("Classifier Test", test_classifier),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print('='*60)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except KeyboardInterrupt:
            logger.warning("\nTest interrupted by user")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Test crashed: {e}")
            results.append((test_name, False))
    
    # Ask if user wants to run mini pipeline
    print("\n" + "="*60)
    print("All component tests complete!")
    print("="*60)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    if all(result for _, result in results):
        print("\n✓ All tests passed!")
        
        print("\nWould you like to run a mini pipeline test (3 URLs)? (y/n)")
        choice = input("> ").strip().lower()
        
        if choice == 'y':
            run_mini_pipeline()
    else:
        print("\n⚠ Some tests failed. Please fix errors before running the full pipeline.")
        print("\nCommon fixes:")
        print("  - Install missing packages: pip install -r requirements.txt")
        print("  - Check internet connection for web scraping")
        print("  - Ensure allUrls.txt exists with valid URLs")


if __name__ == "__main__":
    main()
