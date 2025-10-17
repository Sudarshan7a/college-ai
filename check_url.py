"""
Simple URL Checker - Fast way to test if a URL is meaningful

Usage:
    python check_url.py <url>

Examples:
    python check_url.py https://sdit.ac.in/sports/
    python check_url.py https://sdit.ac.in/rakshitha-b-k-3/
"""

import sys
from src.data_fetcher import DataFetcher


def quick_check(url: str):
    """Quick check - will it be saved or skipped?"""
    
    print(f"\n🔍 Checking: {url}\n")
    
    try:
        # Create fetcher with template
        fetcher = DataFetcher(
            template_url="https://sdit.ac.in/rakshitha-b-k-3/",
            similarity_threshold=0.7
        )
        
        # Fetch page
        soup, error = fetcher.fetch_page(url)
        if error:
            print(f"❌ ERROR: {error}")
            return
        
        # Extract content
        text = fetcher.content_filter.extract_main_content(soup)
        
        # Check if meaningful
        is_meaningful, reason = fetcher.content_filter.is_meaningful(soup, text)
        
        # Show results
        print("=" * 60)
        if is_meaningful:
            print("✅ WILL BE SAVED")
        else:
            print("❌ WILL BE SKIPPED")
        print("=" * 60)
        
        print(f"\nReason: {reason}")
        
        # Show details
        print(f"\nDetails:")
        print(f"  • Text length: {len(text)} chars")
        print(f"  • Paragraphs: {len(soup.find_all('p'))}")
        print(f"  • Sentences: {len(text.split('.'))}")
        
        # Show template similarity if available
        if fetcher.content_filter.template_matcher.template_text:
            _, score = fetcher.content_filter.template_matcher.is_similar_to_template(
                text, similarity_threshold=1.0  # Get raw score
            )
            print(f"  • Template similarity: {score:.1%}")
        
        print("\n")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")


def compare_urls(urls: list):
    """Compare multiple URLs and show results"""
    
    print(f"\n🔍 Checking {len(urls)} URLs...\n")
    
    saved = 0
    skipped = 0
    
    for url in urls:
        try:
            fetcher = DataFetcher(
                template_url="https://sdit.ac.in/rakshitha-b-k-3/",
                similarity_threshold=0.7
            )
            
            soup, error = fetcher.fetch_page(url)
            if error:
                print(f"  ❌ {url}")
                skipped += 1
                continue
            
            text = fetcher.content_filter.extract_main_content(soup)
            is_meaningful, _ = fetcher.content_filter.is_meaningful(soup, text)
            
            if is_meaningful:
                print(f"  ✅ {url}")
                saved += 1
            else:
                print(f"  ❌ {url}")
                skipped += 1
        
        except Exception as e:
            print(f"  ⚠️  {url} - Error: {str(e)[:50]}")
            skipped += 1
    
    print(f"\n{'='*60}")
    print(f"Summary: {saved} saved, {skipped} skipped ({saved/(saved+skipped)*100:.0f}% saved)")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == "compare" and len(sys.argv) > 2:
            # Compare multiple URLs
            compare_urls(sys.argv[2:])
        else:
            # Single URL
            quick_check(sys.argv[1])
    else:
        print(__doc__)
        print("\nExample usage:")
        print("  python check_url.py https://sdit.ac.in/sports/")
        print("  python check_url.py compare https://sdit.ac.in/sports/ https://sdit.ac.in/clubs/")
