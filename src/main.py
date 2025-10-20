"""
Main orchestration script for web scraping and categorization pipeline.

Coordinates URL reading, scraping, classification, saving, Git commits,
and metadata logging.
"""

import csv
import logging
from pathlib import Path
from typing import Optional
import sys

import pandas as pd

from src.config import (
    DATA_DIR,
    EXTRACTED_DATA_DIR,
    CSV_LOG_FILE,
    LOG_LEVEL
)
from src.scraper import WebScraper
from src.classifier import PageClassifier


# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scraping.log', encoding='utf-8')
    ]
)

# Fix Windows console encoding issues
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass  # Fallback to default if reconfiguration fails

logger = logging.getLogger(__name__)


class DataPipeline:
    """
    Orchestrates the complete data extraction and categorization pipeline.
    
    Responsibilities:
    - Read URLs from input file
    - Scrape and extract content
    - Classify pages
    - Save to structured folders
    - Log metadata to CSV
    - Make incremental Git commits
    """
    
    def __init__(self, urls_file: str = "allUrls.txt"):
        """
        Initialize DataPipeline.
        
        Args:
            urls_file: Path to file containing URLs (one per line)
        """
        self.urls_file = Path(urls_file)
        self.data_dir = Path(EXTRACTED_DATA_DIR)
        self.csv_log_file = Path(CSV_LOG_FILE)
        
        # Initialize components
        self.scraper = WebScraper()
        self.classifier = PageClassifier()
        
        # Statistics
        self.stats = {
            "total": 0,
            "scraped": 0,
            "classified": 0,
            "saved": 0,
            "failed": 0,
            "duplicates": 0,
            "low_quality": 0
        }
        
        # Ensure directories exist
        self._setup_directories()
        
        # Initialize CSV log
        self._initialize_csv()
    
    def _setup_directories(self) -> None:
        """Create necessary directories."""
        # Create main data directory
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create category directories
        categories = self.classifier.get_all_categories()
        for category in categories:
            category_dir = self.data_dir / category
            category_dir.mkdir(exist_ok=True)
            logger.debug(f"Created directory: {category_dir}")
        
        # Create directory for CSV log
        self.csv_log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _initialize_csv(self) -> None:
        """Initialize CSV log file with headers."""
        if not self.csv_log_file.exists():
            logger.info(f"Creating new CSV log: {self.csv_log_file}")
            
            with open(self.csv_log_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "id",
                    "title",
                    "source_url",
                    "category",
                    "tag",
                    "source_file",
                    "tags",
                    "word_count",
                    "confidence"
                ])
            
            logger.info(f"Initialized CSV log: {self.csv_log_file}")
    
    def _read_urls(self) -> list[str]:
        """
        Read URLs from input file.
        
        Returns:
            List of URLs
        """
        if not self.urls_file.exists():
            logger.error(f"URLs file not found: {self.urls_file}")
            return []
        
        logger.info(f"Reading URLs from: {self.urls_file}")
        
        urls = []
        # Use utf-8-sig to handle BOM if present
        with open(self.urls_file, 'r', encoding='utf-8-sig') as f:
            for line in f:
                url = line.strip()
                if url and not url.startswith('#'):
                    urls.append(url)
        
        logger.info(f"Loaded {len(urls)} URLs")
        return urls
    
    def _save_content(
        self,
        text: str,
        category: str,
        page_name: str
    ) -> Path:
        """
        Save extracted text to file.
        
        Args:
            text: Text content to save
            category: Category name
            page_name: Page name for filename
            
        Returns:
            Path to saved file
        """
        # Create filename
        category_dir = self.data_dir / category
        file_path = category_dir / f"{page_name}.txt"
        
        # Handle duplicate filenames
        counter = 1
        while file_path.exists():
            file_path = category_dir / f"{page_name}_{counter}.txt"
            counter += 1
        
        # Save content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        logger.info(f"Saved content to: {file_path}")
        
        return file_path
    
    def _log_to_csv(
        self,
        page_id: int,
        title: str,
        url: str,
        category: str,
        tag: str,
        file_path: Path,
        word_count: int,
        confidence: float
    ) -> None:
        """
        Log page metadata to CSV.
        
        Args:
            page_id: Unique page ID
            title: Page title
            url: Source URL
            category: Category name
            tag: Category tag
            file_path: Path to saved text file
            word_count: Word count
            confidence: Classification confidence
        """
        # Generate tags based on category keywords
        category_info = self.classifier.get_category_info(category)
        tags = ", ".join(category_info.get("keywords", [])[:5])
        
        # Get relative path for source_file
        try:
            relative_path = file_path.relative_to(Path.cwd())
        except ValueError:
            relative_path = file_path
        
        # Append to CSV
        with open(self.csv_log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                page_id,
                title,
                url,
                category,
                tag,
                str(relative_path),
                tags,
                word_count,
                f"{confidence:.2f}"
            ])
        
        logger.debug(f"Logged to CSV: ID={page_id}, Category={category}")
    
    def process_url(self, url: str, page_id: int) -> bool:
        """
        Process a single URL through the complete pipeline.
        
        Args:
            url: URL to process
            page_id: Unique page ID
            
        Returns:
            True if processing successful, False otherwise
        """
        try:
            # Step 1: Scrape
            scraped_data = self.scraper.scrape(url)
            
            if not scraped_data:
                self.stats["failed"] += 1
                return False
            
            self.stats["scraped"] += 1
            
            # Step 2: Classify
            category, tag, confidence = self.classifier.classify(
                scraped_data["text"],
                scraped_data["url"],
                scraped_data["title"]
            )
            
            self.stats["classified"] += 1
            
            # Step 3: Save content
            file_path = self._save_content(
                scraped_data["text"],
                category,
                scraped_data["page_name"]
            )
            
            self.stats["saved"] += 1
            
            # Step 4: Log to CSV
            self._log_to_csv(
                page_id,
                scraped_data["title"],
                scraped_data["url"],
                category,
                tag,
                file_path,
                scraped_data["metadata"]["word_count"],
                confidence
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing {url}: {e}", exc_info=True)
            self.stats["failed"] += 1
            return False
    
    def run(self) -> None:
        """Run the complete pipeline."""
        print("\n" + "="*60)
        print("STARTING DATA EXTRACTION PIPELINE")
        print("="*60 + "\n")
        
        # Read URLs
        urls = self._read_urls()
        
        if not urls:
            print("ERROR: No URLs to process. Exiting.")
            return
        
        self.stats["total"] = len(urls)
        print(f"Total URLs to process: {len(urls)}\n")
        
        # Process each URL
        for idx, url in enumerate(urls, start=1):
            print(f"[{idx}/{len(urls)}] {url}...", end=" ", flush=True)
            success = self.process_url(url, idx)
            print("✓" if success else "✗")
        
        # Final summary
        print("\n" + "="*60)
        print("PIPELINE COMPLETE")
        print("="*60)
        print(f"Total:      {self.stats['total']}")
        print(f"Saved:      {self.stats['saved']}")
        print(f"Skipped:    {self.stats['failed']}")
        print("="*60 + "\n")
        
        # Print final summary
        self._print_summary()
    
    def _print_summary(self) -> None:
        """Print pipeline execution summary."""
        logger.info("\n" + "="*60)
        logger.info("PIPELINE EXECUTION SUMMARY")
        logger.info("="*60)
        logger.info(f"Total URLs:        {self.stats['total']}")
        logger.info(f"Successfully scraped: {self.stats['scraped']}")
        logger.info(f"Successfully classified: {self.stats['classified']}")
        logger.info(f"Successfully saved: {self.stats['saved']}")
        logger.info(f"Failed:            {self.stats['failed']}")
        logger.info("="*60)
        
        logger.info("\n✓ Pipeline execution completed!\n")
    
    def _generate_summary_file(self) -> None:
        """Create a final summary commit."""
        summary_file = Path("PIPELINE_SUMMARY.txt")
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("DATA EXTRACTION PIPELINE SUMMARY\n")
            f.write("="*60 + "\n\n")
            f.write(f"Total URLs processed: {self.stats['total']}\n")
            f.write(f"Successfully scraped: {self.stats['scraped']}\n")
            f.write(f"Successfully classified: {self.stats['classified']}\n")
            f.write(f"Successfully saved: {self.stats['saved']}\n")
            f.write(f"Failed: {self.stats['failed']}\n\n")
            
            # Category breakdown
            if self.csv_log_file.exists():
                df = pd.read_csv(self.csv_log_file)
                f.write("Category Breakdown:\n")
                f.write("-" * 40 + "\n")
                category_counts = df['category'].value_counts()
                for category, count in category_counts.items():
                    f.write(f"  {category}: {count}\n")
        
        logger.info(f"Summary file created: {summary_file}")


def main():
    """Main entry point."""
    try:
        pipeline = DataPipeline()
        pipeline.run()
        
    except KeyboardInterrupt:
        logger.warning("\n\nPipeline interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
