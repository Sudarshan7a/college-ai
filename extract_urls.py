"""
Extract all URLs from sitemaps and save to a text file.
"""

from src.data_fetcher import SitemapParser
from src.config import SITEMAPS
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def extract_all_urls(sitemaps, output_file="urls.txt"):
    """
    Extract all URLs from given sitemaps and save to a text file.
    
    Args:
        sitemaps: List of sitemap URLs
        output_file: Output filename (default: urls.txt)
    
    Returns:
        dict: Statistics about extraction
    """
    all_urls = []
    sitemap_stats = {}
    
    logger.info("="*70)
    logger.info("EXTRACTING URLs FROM SITEMAPS")
    logger.info("="*70)
    logger.info("")
    
    # Process each sitemap
    for sitemap_url in sitemaps:
        logger.info(f"Processing: {sitemap_url}")
        
        try:
            urls = SitemapParser.get_urls_from_sitemap(sitemap_url)
            count = len(urls)
            sitemap_stats[sitemap_url] = count
            all_urls.extend(urls)
            
            logger.info(f"  ✓ Found {count} URLs")
            
        except Exception as e:
            logger.warning(f"  ✗ Error: {str(e)}")
            sitemap_stats[sitemap_url] = 0
    
    # Remove duplicates while preserving order
    unique_urls = []
    seen = set()
    for url in all_urls:
        if url not in seen:
            unique_urls.append(url)
            seen.add(url)
    
    # Save to file
    logger.info("")
    logger.info(f"Saving URLs to: {output_file}")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"# URLs extracted from sitemaps\n")
            f.write(f"# Total URLs: {len(unique_urls)}\n")
            f.write(f"# Date: {logger.root.handlers[0].formatter.formatTime(logging.LogRecord('', 0, '', 0, '', (), None))}\n")
            f.write(f"\n")
            
            # Write each URL
            for url in unique_urls:
                f.write(f"{url}\n")
        
        logger.info(f"  ✓ Saved {len(unique_urls)} unique URLs")
        
    except Exception as e:
        logger.error(f"  ✗ Error saving file: {str(e)}")
        return None
    
    # Print summary
    logger.info("")
    logger.info("="*70)
    logger.info("EXTRACTION SUMMARY")
    logger.info("="*70)
    logger.info(f"Total sitemaps processed:  {len(sitemaps)}")
    logger.info(f"Total URLs found:          {len(all_urls)}")
    logger.info(f"Unique URLs:               {len(unique_urls)}")
    logger.info(f"Duplicates removed:        {len(all_urls) - len(unique_urls)}")
    logger.info("")
    logger.info("URLs per sitemap:")
    for sitemap_url, count in sitemap_stats.items():
        sitemap_name = sitemap_url.split('/')[-1]
        logger.info(f"  • {sitemap_name:<25} {count:>4} URLs")
    logger.info("="*70)
    
    return {
        'total_sitemaps': len(sitemaps),
        'total_urls': len(all_urls),
        'unique_urls': len(unique_urls),
        'duplicates': len(all_urls) - len(unique_urls),
        'sitemap_stats': sitemap_stats,
        'output_file': output_file
    }


if __name__ == "__main__":
    import sys
    
    # Allow custom output filename
    output_file = sys.argv[1] if len(sys.argv) > 1 else "urls.txt"
    
    # Extract URLs from configured sitemaps
    stats = extract_all_urls(SITEMAPS, output_file)
    
    if stats:
        print(f"\n✅ Success! URLs saved to: {output_file}")
        print(f"📊 {stats['unique_urls']} unique URLs ready for processing")
    else:
        print("\n❌ Failed to extract URLs")
        sys.exit(1)
