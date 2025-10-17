"""
Data Fetcher Module

Handles fetching data from URLs, sitemaps, and processing web content.
Filters meaningful content based on configurable criteria.
"""

import os
import logging
import xml.etree.ElementTree as ET
from typing import List, Tuple, Optional
from urllib.parse import urljoin, urlparse
from difflib import SequenceMatcher

import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TemplateMatcher:
    """Match and filter pages similar to empty templates."""
    
    def __init__(self, template_text: Optional[str] = None):
        """
        Initialize template matcher.
        
        Args:
            template_text: Text content of empty template page
        """
        self.template_text = template_text
        self.template_words = None
        if template_text:
            self.template_words = set(template_text.lower().split())
    
    def set_template(self, template_text: str):
        """Update the template text."""
        self.template_text = template_text
        self.template_words = set(template_text.lower().split())
    
    def is_similar_to_template(self, text: str, similarity_threshold: float = 0.7) -> Tuple[bool, float]:
        """
        Check if text is similar to empty template (structure/content overlap).
        
        Args:
            text: Text to compare with template
            similarity_threshold: Threshold for considering pages similar (0.0-1.0)
            
        Returns:
            Tuple of (is_similar, similarity_score)
        """
        if not self.template_text or not self.template_words:
            return False, 0.0
        
        # Extract words from current text
        words_text = set(text.lower().split())
        
        if not words_text:
            return True, 1.0
        
        # Calculate word overlap similarity
        common_words = words_text & self.template_words
        similarity = len(common_words) / max(len(words_text), 1)
        
        return similarity >= similarity_threshold, similarity
    
    def fetch_template(self, template_url: str, timeout: int = 10) -> bool:
        """
        Fetch and set template from a URL.
        
        Args:
            template_url: URL of empty/template page
            timeout: Request timeout in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.get(template_url, timeout=timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'footer']):
                script.decompose()
            
            template_text = soup.get_text(separator=' ', strip=True)
            self.set_template(template_text)
            
            logger.info(f"Template loaded from {template_url} ({len(template_text)} chars)")
            return True
        
        except Exception as e:
            logger.error(f"Error fetching template from {template_url}: {e}")
            return False


class ContentFilter:
    """Filter and validate page content based on template matching only."""
    
    def __init__(
        self,
        template_matcher: Optional[TemplateMatcher] = None
    ):
        """
        Initialize content filter.
        
        Args:
            template_matcher: TemplateMatcher instance for template comparison
        """
        self.template_matcher = template_matcher or TemplateMatcher()
    
    def is_meaningful(self, soup: BeautifulSoup, text: str) -> Tuple[bool, str]:
        """
        Check if page content is meaningful based on template matching only.
        
        Args:
            soup: BeautifulSoup parsed HTML
            text: Extracted text content
            
        Returns:
            Tuple of (is_meaningful, reason)
        """
        text_stripped = text.strip()
        
        # Check template similarity (if template is available)
        if self.template_matcher.template_text:
            is_similar, similarity = self.template_matcher.is_similar_to_template(
                text_stripped, 
                similarity_threshold=0.7
            )
            if is_similar:
                return False, f"Similar to empty template (similarity: {similarity:.2%})"
            else:
                return True, f"Different from template (similarity: {similarity:.2%})"
        
        # If no template is set, accept all pages
        return True, "No template configured - accepting all pages"
    
    def extract_main_content(self, soup: BeautifulSoup) -> str:
        """
        Extract main content from page, excluding header/footer/sidebar.
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            Extracted text content
        """
        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'footer']):
            script.decompose()
        
        # Try to find main content area
        main_content = soup.find(['main', 'article', 'div.content'])
        if main_content:
            text = main_content.get_text()
        else:
            text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text


class SitemapParser:
    """Parse and extract URLs from XML sitemaps."""
    
    @staticmethod
    def get_urls_from_sitemap(sitemap_url: str, timeout: int = 10) -> List[str]:
        """
        Extract all URLs from a sitemap.
        
        Args:
            sitemap_url: URL of the sitemap
            timeout: Request timeout in seconds
            
        Returns:
            List of URLs found in sitemap
        """
        try:
            response = requests.get(sitemap_url, timeout=timeout)
            response.raise_for_status()
            
            tree = ET.fromstring(response.content)
            namespace = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            urls = []
            for loc in tree.findall('.//sm:loc', namespace):
                if loc.text:
                    urls.append(loc.text)
            
            logger.info(f"Found {len(urls)} URLs in {sitemap_url}")
            return urls
        
        except requests.RequestException as e:
            logger.error(f"Error fetching sitemap {sitemap_url}: {e}")
            return []
        except ET.ParseError as e:
            logger.error(f"Error parsing sitemap XML {sitemap_url}: {e}")
            return []


class DataFetcher:
    """Main class for fetching and processing web data."""
    
    def __init__(
        self,
        output_dir: str = "data/raw_pages",
        content_filter: Optional[ContentFilter] = None,
        timeout: int = 10,
        user_agent: Optional[str] = None,
        template_url: Optional[str] = None,
        similarity_threshold: float = 0.7
    ):
        """
        Initialize DataFetcher.
        
        Args:
            output_dir: Directory to save fetched content
            content_filter: ContentFilter instance for validation
            timeout: Request timeout in seconds
            user_agent: Custom user agent string
            template_url: URL of empty template page to filter similar pages
            similarity_threshold: Threshold for template similarity (0.0-1.0)
        """
        self.output_dir = output_dir
        self.timeout = timeout
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        self.similarity_threshold = similarity_threshold
        
        # Initialize template matcher and fetch template if URL provided
        template_matcher = TemplateMatcher()
        if template_url:
            template_matcher.fetch_template(template_url, timeout)
        
        # Initialize content filter
        self.content_filter = content_filter or ContentFilter(
            template_matcher=template_matcher
        )
        
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Output directory: {self.output_dir}")
    
    def _get_headers(self) -> dict:
        """Get HTTP headers for requests."""
        return {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
    
    def fetch_page(self, url: str) -> Tuple[Optional[BeautifulSoup], Optional[str]]:
        """
        Fetch and parse a single page.
        
        Args:
            url: URL to fetch
            
        Returns:
            Tuple of (BeautifulSoup object, error_message)
        """
        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup, None
        
        except requests.RequestException as e:
            error_msg = f"Error fetching {url}: {e}"
            logger.warning(error_msg)
            return None, error_msg
    
    def save_content(self, url: str, content: str, index: int) -> str:
        """
        Save content to file.
        
        Args:
            url: Source URL
            content: Text content to save
            index: Page index for filename
            
        Returns:
            Path to saved file
        """
        # Create safe filename from URL
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.replace('www.', '')
        path_slug = parsed_url.path.strip('/').replace('/', '_')
        filename = f"page_{index:04d}_{domain}_{path_slug[:30]}.txt"
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"URL: {url}\n")
                f.write("=" * 80 + "\n\n")
                f.write(content)
            
            logger.info(f"Saved: {filename}")
            return filepath
        
        except Exception as e:
            logger.error(f"Error saving file {filename}: {e}")
            return ""
    
    def fetch_from_sitemaps(self, sitemap_urls: List[str]) -> dict:
        """
        Fetch and process all URLs from multiple sitemaps.
        
        Args:
            sitemap_urls: List of sitemap URLs
            
        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_pages': 0,
            'meaningful_pages': 0,
            'empty_pages': 0,
            'errors': 0,
            'files_saved': []
        }
        
        all_urls = []
        
        # Extract URLs from all sitemaps
        for sitemap_url in sitemap_urls:
            urls = SitemapParser.get_urls_from_sitemap(sitemap_url, self.timeout)
            all_urls.extend(urls)
        
        logger.info(f"Total URLs found: {len(all_urls)}")
        
        # Process each URL
        for index, url in enumerate(all_urls, 1):
            stats['total_pages'] += 1
            
            soup, error = self.fetch_page(url)
            if error:
                stats['errors'] += 1
                continue
            
            # Extract and validate content
            text = self.content_filter.extract_main_content(soup)
            is_meaningful, reason = self.content_filter.is_meaningful(soup, text)
            
            if is_meaningful:
                filepath = self.save_content(url, text, index)
                stats['meaningful_pages'] += 1
                stats['files_saved'].append(filepath)
            else:
                stats['empty_pages'] += 1
                logger.debug(f"Skipped {url}: {reason}")
        
        return stats
    
    def fetch_urls(self, urls: List[str]) -> dict:
        """
        Fetch and process a list of URLs.
        
        Args:
            urls: List of URLs to fetch
            
        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_pages': 0,
            'meaningful_pages': 0,
            'empty_pages': 0,
            'errors': 0,
            'files_saved': []
        }
        
        for index, url in enumerate(urls, 1):
            stats['total_pages'] += 1
            
            soup, error = self.fetch_page(url)
            if error:
                stats['errors'] += 1
                continue
            
            # Extract and validate content
            text = self.content_filter.extract_main_content(soup)
            is_meaningful, reason = self.content_filter.is_meaningful(soup, text)
            
            if is_meaningful:
                filepath = self.save_content(url, text, index)
                stats['meaningful_pages'] += 1
                stats['files_saved'].append(filepath)
            else:
                stats['empty_pages'] += 1
                logger.debug(f"Skipped {url}: {reason}")
        
        return stats


if __name__ == "__main__":
    # Example usage
    print("Data Fetcher Module loaded successfully!")
