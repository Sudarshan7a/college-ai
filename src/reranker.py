"""
Re-ranker Module for College AI
Uses CrossEncoder to re-rank retrieval results for better accuracy.
"""

from pathlib import Path
from typing import List, Dict, Any
import sys
import os

# Suppress TensorFlow warnings
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sentence_transformers import CrossEncoder


class SemanticReranker:
    """
    Re-ranks search results using a CrossEncoder model.
    CrossEncoders are more accurate than bi-encoders for ranking.
    """
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize the re-ranker.
        
        Args:
            model_name: CrossEncoder model name
        """
        self.model_name = model_name
        print(f"[INFO] Loading re-ranker model: {model_name}")
        self.model = CrossEncoder(model_name)
        print(f"[SUCCESS] Re-ranker loaded!")
    
    def rerank(self, query: str, results: List[Dict[str, Any]], top_k: int = None) -> List[Dict[str, Any]]:
        """
        Re-rank search results based on query relevance.
        
        Args:
            query: Search query text
            results: List of result dictionaries with 'metadata' containing 'text'
            top_k: Number of top results to return (if None, returns all)
            
        Returns:
            Re-ranked list of results with added 'rerank_score' field
        """
        if not results:
            return []
        
        # Extract texts from results
        texts = [r['metadata']['text'] for r in results]
        
        # Create query-document pairs
        pairs = [[query, text] for text in texts]
        
        # Score with CrossEncoder
        scores = self.model.predict(pairs)
        
        # Add scores to results and sort
        reranked_results = []
        for result, score in zip(results, scores):
            result['rerank_score'] = float(score)
            reranked_results.append(result)
        
        # Sort by rerank score (higher is better)
        reranked_results.sort(key=lambda x: x['rerank_score'], reverse=True)
        
        # Return top_k if specified
        if top_k:
            reranked_results = reranked_results[:top_k]
        
        return reranked_results
    
    def rerank_with_comparison(self, query: str, results: List[Dict[str, Any]], 
                               top_k: int = None) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Re-rank results and provide comparison statistics.
        
        Args:
            query: Search query
            results: Original results
            top_k: Number of results to return
            
        Returns:
            Tuple of (reranked_results, stats_dict)
        """
        reranked = self.rerank(query, results, top_k)
        
        # Calculate statistics
        original_order = [r['index'] for r in results]
        reranked_order = [r['index'] for r in reranked]
        
        changes = sum(1 for i, (orig, rerank) in enumerate(zip(original_order, reranked_order)) 
                     if orig != rerank)
        
        stats = {
            'total_results': len(results),
            'reranked_count': len(reranked),
            'order_changes': changes,
            'change_percentage': (changes / len(results) * 100) if results else 0
        }
        
        return reranked, stats


def create_reranker(model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> SemanticReranker:
    """
    Convenience function to create a reranker.
    
    Args:
        model_name: CrossEncoder model name
        
    Returns:
        SemanticReranker instance
    """
    return SemanticReranker(model_name=model_name)


# Example usage
if __name__ == "__main__":
    print("="*60)
    print("RE-RANKER DEMO")
    print("="*60)
    
    # Create reranker
    reranker = create_reranker()
    
    # Sample query and results
    query = "What are the placement statistics?"
    
    sample_results = [
        {
            'index': 0,
            'distance': 1.2,
            'metadata': {
                'text': 'The library has 50,000 books and is open from 8 AM to 10 PM daily.',
                'category': 'facilities'
            }
        },
        {
            'index': 1,
            'distance': 1.1,
            'metadata': {
                'text': 'Computer Science department offers AI and Data Science programs.',
                'category': 'departments'
            }
        },
        {
            'index': 2,
            'distance': 0.9,
            'metadata': {
                'text': 'The placement cell achieved 95% placements in 2024 with average package of 6.5 LPA. Top recruiters include TCS, Infosys, and Amazon.',
                'category': 'placements'
            }
        }
    ]
    
    print(f"\n🔍 Query: '{query}'")
    print("\n📊 Original Results (sorted by FAISS distance):")
    for i, result in enumerate(sample_results, 1):
        print(f"{i}. Distance: {result['distance']:.2f} | {result['metadata']['category']}")
        print(f"   {result['metadata']['text'][:80]}...")
    
    # Re-rank
    reranked, stats = reranker.rerank_with_comparison(query, sample_results)
    
    print("\n✨ Re-ranked Results (sorted by semantic relevance):")
    for i, result in enumerate(reranked, 1):
        print(f"{i}. Rerank Score: {result['rerank_score']:.4f} | Distance: {result['distance']:.2f}")
        print(f"   Category: {result['metadata']['category']}")
        print(f"   {result['metadata']['text'][:80]}...")
    
    print(f"\n📈 Statistics:")
    print(f"   Order changes: {stats['order_changes']}/{stats['total_results']} ({stats['change_percentage']:.0f}%)")
    
    print("\n" + "="*60)
    print("✅ Re-ranking improves relevance!")
    print("   FAISS Distance: Fast but approximate")
    print("   CrossEncoder Score: Slower but more accurate")
    print("="*60)
