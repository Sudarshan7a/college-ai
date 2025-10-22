"""
Hybrid page classifier using rule-based and semantic similarity.

Categorizes pages into predefined categories using keyword matching
and sentence-transformers embeddings.
"""

import logging
from typing import Optional, Tuple
import warnings

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from src.config import CATEGORIES, SEMANTIC_SIMILARITY_THRESHOLD


logger = logging.getLogger(__name__)

# Suppress warnings from transformers
warnings.filterwarnings("ignore", category=FutureWarning)


class PageClassifier:
    """
    Hybrid classifier for categorizing web pages.
    
    Uses a two-stage approach:
    1. Rule-based keyword matching
    2. Semantic similarity with sentence embeddings
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize PageClassifier.
        
        Args:
            model_name: Name of sentence-transformers model to use
        """
        self.categories = CATEGORIES
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self.category_embeddings: Optional[dict] = None
        
        # Load model lazily
        self._model_loaded = False
    
    def _load_model(self) -> None:
        """Load sentence-transformers model and compute category embeddings."""
        if self._model_loaded:
            return
        
        try:
            logger.info(f"Loading sentence-transformers model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            
            # Precompute embeddings for category descriptions
            self.category_embeddings = {}
            
            for category_name, category_info in self.categories.items():
                # Combine description and keywords for richer representation
                text = f"{category_info['description']}. Keywords: {', '.join(category_info['keywords'])}"
                embedding = self.model.encode(text, convert_to_tensor=False)
                self.category_embeddings[category_name] = embedding
            
            self._model_loaded = True
            logger.info("Model loaded and category embeddings computed")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None
            self.category_embeddings = None
    
    def _rule_based_classify(self, text: str, url: str) -> Optional[str]:
        """
        Classify using rule-based keyword matching.
        
        Args:
            text: Page text content
            url: Page URL
            
        Returns:
            Category name if confident match, None otherwise
        """
        text_lower = text.lower()
        url_lower = url.lower()
        
        # Combine text and URL for matching
        combined = f"{url_lower} {text_lower}"
        
        # Count keyword matches for each category
        scores = {}
        
        for category_name, category_info in self.categories.items():
            keywords = category_info["keywords"]
            matches = sum(1 for keyword in keywords if keyword in combined)
            
            # Normalize by number of keywords
            score = matches / len(keywords) if keywords else 0
            scores[category_name] = score
        
        # Find best match
        if scores:
            best_category = max(scores, key=scores.get)
            best_score = scores[best_category]
            
            logger.debug(f"Rule-based scores: {scores}")
            
            # Require at least 20% keyword match for confidence
            if best_score >= 0.2:
                logger.info(
                    f"Rule-based classification: {best_category} "
                    f"(score: {best_score:.3f})"
                )
                return best_category
        
        return None
    
    def _semantic_classify(self, text: str, url: str) -> Optional[str]:
        """
        Classify using semantic similarity with embeddings.
        
        Args:
            text: Page text content
            url: Page URL
            
        Returns:
            Category name if confident match, None otherwise
        """
        if not self._model_loaded:
            self._load_model()
        
        if not self.model or not self.category_embeddings:
            logger.warning("Semantic model not available")
            return None
        
        try:
            # Create embedding for page content
            # Use first 500 words to avoid memory issues
            words = text.split()[:500]
            text_sample = " ".join(words)
            
            # Include URL in text for context
            combined_text = f"{url}. {text_sample}"
            
            text_embedding = self.model.encode(
                combined_text, 
                convert_to_tensor=False
            )
            
            # Calculate similarities
            similarities = {}
            
            for category_name, category_embedding in self.category_embeddings.items():
                similarity = cosine_similarity(
                    [text_embedding],
                    [category_embedding]
                )[0][0]
                similarities[category_name] = float(similarity)
            
            logger.debug(f"Semantic similarities: {similarities}")
            
            # Find best match
            best_category = max(similarities, key=similarities.get)
            best_similarity = similarities[best_category]
            
            # Check if similarity is above threshold
            if best_similarity >= SEMANTIC_SIMILARITY_THRESHOLD:
                logger.info(
                    f"Semantic classification: {best_category} "
                    f"(similarity: {best_similarity:.3f})"
                )
                return best_category
            else:
                logger.info(
                    f"Semantic similarity too low: {best_similarity:.3f} < "
                    f"{SEMANTIC_SIMILARITY_THRESHOLD}"
                )
        
        except Exception as e:
            logger.error(f"Error in semantic classification: {e}")
        
        return None
    
    def classify(
        self, 
        text: str, 
        url: str, 
        title: Optional[str] = None
    ) -> Tuple[str, str, float]:
        """
        Classify page using hybrid approach.
        
        Tries rule-based first, falls back to semantic similarity.
        
        Args:
            text: Page text content
            url: Page URL
            title: Page title (optional, used for context)
            
        Returns:
            Tuple of (category_name, tag, confidence)
        """
        logger.info(f"Classifying: {url}")
        
        # Add title to text for better classification
        if title:
            text = f"{title}. {text}"
        
        # Try rule-based classification first
        category = self._rule_based_classify(text, url)
        
        if category:
            return (
                category, 
                self.categories[category]["tag"], 
                0.8  # High confidence for rule-based
            )
        
        # Fall back to semantic classification
        logger.info("Rule-based classification uncertain, trying semantic...")
        category = self._semantic_classify(text, url)
        
        if category:
            return (
                category,
                self.categories[category]["tag"],
                0.6  # Medium confidence for semantic
            )
        
        # Default fallback
        logger.warning(
            f"Could not classify {url} confidently, "
            f"defaulting to 'college_info'"
        )
        return (
            "college_info",
            self.categories["college_info"]["tag"],
            0.3  # Low confidence for default
        )
    
    def get_category_info(self, category: str) -> dict:
        """
        Get information about a category.
        
        Args:
            category: Category name
            
        Returns:
            Category information dictionary
        """
        return self.categories.get(category, {})
    
    def get_all_categories(self) -> list[str]:
        """
        Get list of all category names.
        
        Returns:
            List of category names
        """
        return list(self.categories.keys())
