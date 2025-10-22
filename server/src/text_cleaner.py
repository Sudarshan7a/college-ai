"""
Text Cleaning and Preprocessing for Better Semantic Search
Removes noise, normalizes text, and improves retrieval quality.
"""

import re
from typing import List
from langchain_core.documents import Document


class TextCleaner:
    """
    Cleans and preprocesses text documents for better semantic search.
    """
    
    # Patterns to remove (navigation, menus, common website elements)
    NOISE_PATTERNS = [
        r'Home\s*[»›]\s*',  # Navigation breadcrumbs
        r'Skip to content',
        r'Menu\s*Close',
        r'Search for:',
        r'Copyright\s*©.*',
        r'All rights reserved',
        r'^\s*[A-Z\s]{2,}\s*$',  # All-caps menu items on their own line
        r'Click here',
        r'Read more',
        r'\[.*?\]',  # Remove [brackets] content
    ]
    
    # Patterns that indicate low-value content
    LOW_VALUE_INDICATORS = [
        'lorem ipsum',
        'sample text',
        'placeholder',
        'coming soon',
        'under construction',
    ]
    
    def __init__(self, min_content_length: int = 100):
        """
        Initialize text cleaner.
        
        Args:
            min_content_length: Minimum cleaned text length to keep
        """
        self.min_content_length = min_content_length
        self.compiled_patterns = [re.compile(p, re.IGNORECASE | re.MULTILINE) 
                                 for p in self.NOISE_PATTERNS]
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text content
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove noise patterns
        cleaned = text
        for pattern in self.compiled_patterns:
            cleaned = pattern.sub('', cleaned)
        
        # Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Multiple spaces to single
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)  # Max 2 newlines
        
        # Remove excessive punctuation
        cleaned = re.sub(r'\.{3,}', '...', cleaned)  # Multiple dots
        cleaned = re.sub(r'-{3,}', '---', cleaned)  # Multiple dashes
        
        # Remove URLs (optional - keep if needed for source tracking)
        # cleaned = re.sub(r'http[s]?://\S+', '', cleaned)
        
        # Fix spacing around punctuation
        cleaned = re.sub(r'\s+([.,;:!?])', r'\1', cleaned)
        cleaned = re.sub(r'([.,;:!?])(\w)', r'\1 \2', cleaned)
        
        # Strip leading/trailing whitespace
        cleaned = cleaned.strip()
        
        return cleaned
    
    def is_low_quality(self, text: str) -> bool:
        """
        Check if text is low quality (too short, generic, or placeholder).
        
        Args:
            text: Text to check
            
        Returns:
            True if low quality, False otherwise
        """
        if len(text) < self.min_content_length:
            return True
        
        text_lower = text.lower()
        for indicator in self.LOW_VALUE_INDICATORS:
            if indicator in text_lower:
                return True
        
        # Check if text is mostly navigation/menu items (high ratio of short lines)
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if lines:
            short_lines = sum(1 for l in lines if len(l) < 30)
            if short_lines / len(lines) > 0.7:  # 70% short lines = likely menu
                return True
        
        return False
    
    def clean_document(self, document: Document) -> Document:
        """
        Clean a LangChain Document object.
        
        Args:
            document: Document to clean
            
        Returns:
            Cleaned Document with updated content
        """
        cleaned_text = self.clean_text(document.page_content)
        
        # Create new document with cleaned content
        cleaned_doc = Document(
            page_content=cleaned_text,
            metadata=document.metadata.copy()
        )
        
        # Add cleaning metadata
        cleaned_doc.metadata['cleaned'] = True
        cleaned_doc.metadata['original_length'] = len(document.page_content)
        cleaned_doc.metadata['cleaned_length'] = len(cleaned_text)
        
        return cleaned_doc
    
    def clean_documents(self, documents: List[Document]) -> List[Document]:
        """
        Clean a list of documents, filtering out low-quality ones.
        
        Args:
            documents: List of documents to clean
            
        Returns:
            List of cleaned, high-quality documents
        """
        if not documents:
            return []
        
        print(f"\n[INFO] Cleaning {len(documents)} documents...")
        
        cleaned_docs = []
        skipped = 0
        
        for doc in documents:
            cleaned_doc = self.clean_document(doc)
            
            if self.is_low_quality(cleaned_doc.page_content):
                skipped += 1
                continue
            
            cleaned_docs.append(cleaned_doc)
        
        print(f"[SUCCESS] Kept {len(cleaned_docs)} high-quality documents")
        print(f"[INFO] Skipped {skipped} low-quality documents")
        
        return cleaned_docs
    
    def enhance_metadata(self, document: Document) -> Document:
        """
        Add enhanced metadata for better retrieval context.
        
        Args:
            document: Document to enhance
            
        Returns:
            Document with enhanced metadata
        """
        text = document.page_content
        
        # Count sentences (approximate)
        sentences = len(re.findall(r'[.!?]+', text))
        
        # Count words
        words = len(text.split())
        
        # Extract potential key phrases (capitalized multi-word terms)
        key_phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', text)
        
        # Add to metadata
        document.metadata['sentence_count'] = sentences
        document.metadata['word_count'] = words
        if key_phrases:
            document.metadata['key_phrases'] = key_phrases[:10]  # Top 10
        
        return document


def clean_and_enhance_documents(documents: List[Document],
                                min_content_length: int = 100) -> List[Document]:
    """
    Convenience function to clean and enhance documents.
    
    Args:
        documents: Documents to process
        min_content_length: Minimum length for cleaned content
        
    Returns:
        Cleaned and enhanced documents
    """
    cleaner = TextCleaner(min_content_length=min_content_length)
    
    # Clean documents
    cleaned = cleaner.clean_documents(documents)
    
    # Enhance metadata
    enhanced = [cleaner.enhance_metadata(doc) for doc in cleaned]
    
    return enhanced


# Example usage
if __name__ == "__main__":
    # Example noisy text
    sample_text = """
    Home » SSR 2024 Documents
    
    Skip to content
    
    MENU    CLOSE
    
    Criterion 1 – Curricular Aspects
    
    The Computer Science Department at SDIT has achieved 95% placements 
    in 2024 with an average package of 6.5 LPA.     Top recruiters include 
    TCS, Infosys, and Amazon.
    
    
    
    Click here to read more...
    
    Copyright © 2024 All rights reserved
    """
    
    print("="*60)
    print("TEXT CLEANER DEMO")
    print("="*60)
    
    cleaner = TextCleaner()
    
    print("\n📄 Original Text:")
    print(sample_text)
    print(f"\nLength: {len(sample_text)} chars")
    
    cleaned = cleaner.clean_text(sample_text)
    
    print("\n✨ Cleaned Text:")
    print(cleaned)
    print(f"\nLength: {len(cleaned)} chars")
    print(f"Reduction: {100 - (len(cleaned)/len(sample_text)*100):.1f}%")
