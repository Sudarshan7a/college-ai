"""
Quick test script to process a few URLs from a test file.

Usage:
    python run_test.py
    python run_test.py test_urls.txt
    python run_test.py test_urls.txt 10
"""

import sys
from src.main import DataPipeline

def main():
    # Get parameters
    urls_file = sys.argv[1] if len(sys.argv) > 1 else "allUrls.txt"
    max_urls = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    print(f"\n{'='*60}")
    print(f"Processing {max_urls} URLs from {urls_file}")
    print(f"{'='*60}\n")
    
    # Create pipeline with custom file
    pipeline = DataPipeline(urls_file)
    
    # Read URLs (remove BOM if present)
    with open(urls_file, 'r', encoding='utf-8-sig') as f:
        urls = []
        for line in f:
            url = line.strip()
            if url and not url.startswith('#'):
                urls.append(url)
            if len(urls) >= max_urls:
                break
    
    print(f"URLs to process:")
    for i, url in enumerate(urls, 1):
        print(f"  {i}. {url}")
    
    print("\nStarting...\n")
    
    # Process each URL
    for idx, url in enumerate(urls, 1):
        print(f"[{idx}/{len(urls)}] {url}...", end=" ", flush=True)
        
        success = pipeline.process_url(url, idx)
        
        if success:
            print("✓")
        else:
            print("✗ (skipped)")
    
    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total:      {len(urls)}")
    print(f"Saved:      {pipeline.stats['saved']}")
    print(f"Skipped:    {pipeline.stats['failed']}")
    print(f"{'='*60}")
    
    print(f"\nResults saved to:")
    print(f"  • Text files: data/extracted/<category>/")
    print(f"  • Metadata:   data/data_inventory.csv")
    print(f"  • Logs:       scraping.log")

if __name__ == "__main__":
    main()
