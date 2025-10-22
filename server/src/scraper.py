"""
Web scraper for extracting meaningful content from HTML pages.

Handles downloading, parsing, content extraction, and duplicate detection.
"""

import logging
import re
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, Comment
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.config import (
    REQUEST_TIMEOUT,
    USER_AGENT,
    TEMPLATE_URL,
    TEMPLATE_DUPLICATE_THRESHOLD,
    CONTENT_FILTER
)


logger = logging.getLogger(__name__)


class WebScraper:
    """
    Scrapes web pages and extracts meaningful content.
    
    Features:
    - Downloads HTML with proper headers
    - Removes navigation, headers, footers
    - Extracts clean body text
    - Compares against template to detect duplicates
    """
    
    def __init__(self, template_url: Optional[str] = None):
        """
        Initialize WebScraper.
        
        Args:
            template_url: URL of template page for duplicate detection
        """
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        
        self.template_url = template_url or TEMPLATE_URL
        self.template_text: Optional[str] = None
        
        # Load template on initialization
        if self.template_url:
            self._load_template()
    
    def _load_template(self) -> None:
        """Load and extract text from template page."""
        try:
            logger.info(f"Loading template page: {self.template_url}")
            html = self.download(self.template_url)
            
            if html:
                self.template_text = self._extract_text(html)
                logger.info(
                    f"Template loaded: {len(self.template_text)} characters"
                )
            else:
                logger.warning("Failed to load template page")
                
        except Exception as e:
            logger.error(f"Error loading template: {e}")
    
    def download(self, url: str) -> Optional[str]:
        """
        Download HTML content from URL.
        
        Args:
            url: URL to download
            
        Returns:
            HTML content as string, or None if failed
        """
        try:
            logger.debug(f"Downloading: {url}")
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            logger.debug(
                f"Downloaded {len(response.content)} bytes from {url}"
            )
            return response.text
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout downloading {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading {url}: {e}")
            return None
    
    def _extract_text(self, html: str) -> str:
        """
        Extract clean text from HTML, removing navigation and boilerplate.
        
        Args:
            html: HTML content
            
        Returns:
            Cleaned text content
        """
        soup = BeautifulSoup(html, "lxml")
        
        # Remove script, style, and other non-content tags
        for tag in soup(["script", "style", "meta", "link", "noscript"]):
            tag.decompose()
        
        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Remove common navigation/header/footer elements
        for selector in [
            "nav", "header", "footer", 
            {"class": re.compile(r"nav|menu|header|footer|sidebar", re.I)},
            {"id": re.compile(r"nav|menu|header|footer|sidebar", re.I)},
            {"role": "navigation"},
            {"role": "banner"},
            {"role": "contentinfo"}
        ]:
            for element in soup.find_all(selector):
                element.decompose()
        
        # Extract text from main content
        main_content = soup.find("main") or soup.find("article") or soup.find("body")
        
        if not main_content:
            main_content = soup
        
        # Get text with some structure preserved
        text_parts = []
        
        # Extract from paragraphs and headings
        for tag in main_content.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "li"]):
            text = tag.get_text(strip=True)
            if text and len(text) > 20:  # Skip very short snippets
                text_parts.append(text)
        
        # If no structured content found, fall back to all text
        if not text_parts:
            text_parts = [main_content.get_text(strip=True)]
        
        # Join and clean
        full_text = "\n".join(text_parts)
        full_text = re.sub(r'\n\s*\n', '\n\n', full_text)  # Remove excessive newlines
        full_text = re.sub(r' +', ' ', full_text)  # Remove excessive spaces
        
        return full_text.strip()
    
    def extract_content(self, html: str, url: str) -> Tuple[str, dict]:
        """
        Extract content and metadata from HTML.
        
        Args:
            html: HTML content
            url: Source URL
            
        Returns:
            Tuple of (text_content, metadata_dict)
        """
        soup = BeautifulSoup(html, "lxml")
        
        # Extract title
        title = "Untitled"
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        else:
            h1 = soup.find("h1")
            if h1:
                title = h1.get_text(strip=True)
        
        # Clean title
        title = re.sub(r'\s+', ' ', title)
        title = title[:200]  # Limit length
        
        # Extract main text
        text_content = self._extract_text(html)
        
        # Count structural elements for quality check
        paragraphs = len(soup.find_all("p"))
        headings = len(soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]))
        
        # Create metadata
        metadata = {
            "title": title,
            "url": url,
            "text_length": len(text_content),
            "paragraphs": paragraphs,
            "headings": headings,
            "word_count": len(text_content.split())
        }
        
        return text_content, metadata
    
    def is_quality_content(self, text: str, metadata: dict) -> bool:
        """
        Check if content meets quality thresholds.
        
        Args:
            text: Text content
            metadata: Metadata dictionary
            
        Returns:
            True if content meets quality standards
        """
        # Check text length
        if len(text) < CONTENT_FILTER["min_text_length"]:
            logger.debug(
                f"Content too short: {len(text)} < "
                f"{CONTENT_FILTER['min_text_length']} chars"
            )
            return False
        
        # Check paragraphs
        if metadata["paragraphs"] < CONTENT_FILTER["min_paragraphs"]:
            logger.debug(
                f"Too few paragraphs: {metadata['paragraphs']} < "
                f"{CONTENT_FILTER['min_paragraphs']}"
            )
            return False
        
        # Check sentences
        sentences = len([s for s in text.split('.') if len(s.strip()) > 10])
        if sentences < CONTENT_FILTER["min_sentences"]:
            logger.debug(
                f"Too few sentences: {sentences} < "
                f"{CONTENT_FILTER['min_sentences']}"
            )
            return False
        
        return True
    
    def compare_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts using TF-IDF.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        try:
            if not text1 or not text2:
                return 0.0
            
            # Use TF-IDF vectorization
            vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                lowercase=True
            )
            
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def is_duplicate(self, text: str) -> bool:
        """
        Check if text is similar to template (duplicate/boilerplate).
        
        Args:
            text: Text to check
            
        Returns:
            True if text is too similar to template
        """
        if not self.template_text or not text:
            return False
        
        similarity = self.compare_similarity(text, self.template_text)
        
        logger.debug(f"Template similarity: {similarity:.3f}")
        
        if similarity >= TEMPLATE_DUPLICATE_THRESHOLD:
            logger.info(
                f"Content is duplicate/boilerplate "
                f"(similarity: {similarity:.3f})"
            )
            return True
        
        return False
    
    def get_page_name(self, url: str) -> str:
        """
        Generate a clean filename from URL.
        
        Args:
            url: Source URL
            
        Returns:
            Clean filename (without extension)
        """
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        
        if not path:
            path = "index"
        
        # Clean the path
        path = path.replace("/", "_")
        path = re.sub(r'[^\w\-_]', '', path)
        path = path[:100]  # Limit length
        
        # Remove common extensions
        path = re.sub(r'\.(html?|php|aspx?)$', '', path, flags=re.I)
        
        if not path:
            path = "page"
        
        return path
    
    def scrape(self, url: str) -> Optional[dict]:
        """
        Scrape a URL and return extracted data.
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary with content and metadata, or None if failed
        """
        try:
            logger.info(f"Scraping: {url}")
            
            # Download HTML
            html = self.download(url)
            if not html:
                logger.warning(f"Failed to download {url}")
                return None
            
            # Extract content
            text_content, metadata = self.extract_content(html, url)
            
            # Quality check
            if not self.is_quality_content(text_content, metadata):
                logger.warning(f"Content quality check failed for {url}")
                return None
            
            # Duplicate check
            if self.is_duplicate(text_content):
                logger.warning(f"Duplicate/boilerplate detected: {url}")
                return None
            
            # Generate page name
            page_name = self.get_page_name(url)
            
            result = {
                "url": url,
                "title": metadata["title"],
                "text": text_content,
                "page_name": page_name,
                "metadata": metadata
            }
            
            logger.info(
                f"Successfully scraped {url}: "
                f"{len(text_content)} chars, "
                f"{metadata['word_count']} words"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
