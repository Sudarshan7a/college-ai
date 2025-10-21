"""
FAISS Vector Store for College AI
Builds and queries a FAISS index for semantic search using embeddings.
"""

from pathlib import Path
from typing import List, Any, Dict
import sys
import os
import pickle

# Suppress TensorFlow warnings
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from langchain_core.documents import Document

from src.embeddings import EmbeddingPipeline, create_embeddings_from_documents
from src.data_loader import load_all_documents, load_documents_by_category
from src.config import BASE_PATH, EXTRACTED_DATA_DIR
from src.text_cleaner import clean_and_enhance_documents

# Optional: Import reranker (lazy load to save memory if not used)
try:
    from src.reranker import SemanticReranker
    RERANKER_AVAILABLE = True
except ImportError:
    RERANKER_AVAILABLE = False
    print("[WARNING] Reranker not available. Install: pip install sentence-transformers")


# Configuration
FAISS_STORE_DIR = f"{BASE_PATH}/data/faiss_store"
# Upgraded to MPNet for better semantic understanding
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"  # Better semantic accuracy than MiniLM
CHUNK_SIZE = 2000  # Increased for better context retention
CHUNK_OVERLAP = 300  # More overlap for continuity


class FaissVectorStore:
    """
    FAISS-based vector store for semantic search.
    """
    
    def __init__(self, 
                 persist_dir: str = FAISS_STORE_DIR,
                 embedding_model: str = EMBEDDING_MODEL,
                 chunk_size: int = CHUNK_SIZE,
                 chunk_overlap: int = CHUNK_OVERLAP):
        """
        Initialize FAISS vector store.
        
        Args:
            persist_dir: Directory to save/load FAISS index
            embedding_model: SentenceTransformer model name
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        self.persist_dir = persist_dir
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Create persist directory
        os.makedirs(self.persist_dir, exist_ok=True)
        
        # Initialize FAISS index and metadata
        self.index = None
        self.metadata = []
        
        # Load model for querying
        print(f"[INFO] Loading embedding model: {embedding_model}")
        self.model = SentenceTransformer(embedding_model)
        
        # Optional reranker (lazy loaded on first use)
        self.reranker = None
        self.use_reranker = False
        
        print(f"[INFO] Vector store initialized")
        print(f"[INFO] Persist directory: {self.persist_dir}")
    
    def build_from_documents(self, documents: List[Document], clean_text: bool = True) -> None:
        """
        Build FAISS index from documents.
        
        Args:
            documents: List of LangChain Document objects
            clean_text: Whether to clean and enhance text (recommended)
        """
        if not documents:
            raise ValueError("No documents provided")
        
        print(f"\n[INFO] Building vector store from {len(documents)} documents...")
        
        # Clean and enhance documents for better semantic search
        if clean_text:
            print("[STEP] Cleaning and enhancing documents...")
            documents = clean_and_enhance_documents(documents, min_content_length=100)
            
            if not documents:
                raise ValueError("No documents remaining after cleaning")
        
        # Create embeddings using EmbeddingPipeline
        pipeline = create_embeddings_from_documents(
            documents=documents,
            model_name=self.embedding_model,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        
        # Get embeddings and chunks
        embeddings = pipeline.get_embeddings()
        chunks = pipeline.get_chunks()
        
        # Prepare metadata
        metadatas = []
        for chunk in chunks:
            meta = {
                "text": chunk.page_content,
                "category": chunk.metadata.get("category", "unknown"),
                "filename": chunk.metadata.get("filename", "unknown"),
                "source_path": chunk.metadata.get("source_path", "unknown")
            }
            metadatas.append(meta)
        
        # Add to FAISS index
        self.add_embeddings(embeddings.astype('float32'), metadatas)
        
        # Save to disk
        self.save()
        
        print(f"[SUCCESS] Vector store built and saved to {self.persist_dir}")
    
    def add_embeddings(self, embeddings: np.ndarray, metadatas: List[Dict] = None) -> None:
        """
        Add embeddings to FAISS index.
        
        Args:
            embeddings: Numpy array of embeddings (float32)
            metadatas: List of metadata dictionaries
        """
        if embeddings.dtype != np.float32:
            embeddings = embeddings.astype('float32')
        
        dim = embeddings.shape[1]
        
        # Initialize FAISS index if not exists
        if self.index is None:
            # Using L2 distance (Euclidean)
            self.index = faiss.IndexFlatL2(dim)
            print(f"[INFO] Created FAISS index with dimension: {dim}")
        
        # Add vectors to index
        self.index.add(embeddings)
        
        # Store metadata
        if metadatas:
            self.metadata.extend(metadatas)
        
        print(f"[INFO] Added {embeddings.shape[0]} vectors to FAISS index")
        print(f"[INFO] Total vectors in index: {self.index.ntotal}")
    
    def save(self) -> None:
        """
        Save FAISS index and metadata to disk.
        """
        if self.index is None:
            raise ValueError("No index to save. Build index first.")
        
        faiss_path = os.path.join(self.persist_dir, "faiss.index")
        meta_path = os.path.join(self.persist_dir, "metadata.pkl")
        
        # Save FAISS index
        faiss.write_index(self.index, faiss_path)
        
        # Save metadata
        with open(meta_path, "wb") as f:
            pickle.dump(self.metadata, f)
        
        print(f"\n[SUCCESS] Saved FAISS index to: {faiss_path}")
        print(f"[SUCCESS] Saved metadata to: {meta_path}")
        print(f"[INFO] Total vectors saved: {self.index.ntotal}")
    
    def load(self) -> None:
        """
        Load FAISS index and metadata from disk.
        """
        faiss_path = os.path.join(self.persist_dir, "faiss.index")
        meta_path = os.path.join(self.persist_dir, "metadata.pkl")
        
        if not os.path.exists(faiss_path):
            raise FileNotFoundError(f"FAISS index not found at {faiss_path}")
        
        if not os.path.exists(meta_path):
            raise FileNotFoundError(f"Metadata not found at {meta_path}")
        
        # Load FAISS index
        self.index = faiss.read_index(faiss_path)
        
        # Load metadata
        with open(meta_path, "rb") as f:
            self.metadata = pickle.load(f)
        
        print(f"\n[SUCCESS] Loaded FAISS index from: {faiss_path}")
        print(f"[SUCCESS] Loaded metadata from: {meta_path}")
        print(f"[INFO] Total vectors loaded: {self.index.ntotal}")
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Dict]:
        """
        Search FAISS index with embedding vector.
        
        Args:
            query_embedding: Query embedding vector (2D array)
            top_k: Number of results to return
            
        Returns:
            List of result dictionaries with index, distance, and metadata
        """
        if self.index is None:
            raise ValueError("No index loaded. Call build_from_documents() or load() first.")
        
        if query_embedding.dtype != np.float32:
            query_embedding = query_embedding.astype('float32')
        
        # Ensure 2D array
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Search FAISS index
        distances, indices = self.index.search(query_embedding, top_k)
        
        # Prepare results
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < len(self.metadata):
                result = {
                    "index": int(idx),
                    "distance": float(dist),
                    "metadata": self.metadata[idx]
                }
                results.append(result)
        
        return results
    
    def enable_reranker(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> None:
        """
        Enable re-ranking of search results with CrossEncoder.
        
        Args:
            model_name: CrossEncoder model to use for re-ranking
        """
        if not RERANKER_AVAILABLE:
            raise ImportError("Reranker not available. Install sentence-transformers with CrossEncoder support.")
        
        if self.reranker is None:
            print(f"[INFO] Enabling re-ranker: {model_name}")
            self.reranker = SemanticReranker(model_name=model_name)
        
        self.use_reranker = True
        print("[SUCCESS] Re-ranker enabled!")
    
    def disable_reranker(self) -> None:
        """Disable re-ranking (use only FAISS distances)."""
        self.use_reranker = False
        print("[INFO] Re-ranker disabled")
    
    def query(self, query_text: str, top_k: int = 5, rerank: bool = None) -> List[Dict]:
        """
        Query vector store with text.
        
        Args:
            query_text: Search query text
            top_k: Number of results to return
            rerank: Whether to use re-ranker (if None, uses self.use_reranker setting)
            
        Returns:
            List of result dictionaries (optionally re-ranked)
        """
        if self.index is None:
            raise ValueError("No index loaded. Call build_from_documents() or load() first.")
        
        # Determine if we should rerank
        should_rerank = rerank if rerank is not None else self.use_reranker
        
        print(f"\n[INFO] Querying: '{query_text}'")
        
        # Encode query
        query_embedding = self.model.encode([query_text], normalize_embeddings=True)
        query_embedding = query_embedding.astype('float32')
        
        # Get more results if re-ranking (e.g., top 10 for re-ranking to top 5)
        initial_k = top_k * 2 if should_rerank and self.reranker else top_k
        
        # Search with FAISS
        results = self.search(query_embedding, top_k=initial_k)
        
        print(f"[INFO] Found {len(results)} initial results")
        
        # Re-rank if enabled
        if should_rerank and self.reranker:
            print(f"[INFO] Re-ranking with CrossEncoder...")
            results = self.reranker.rerank(query_text, results, top_k=top_k)
            print(f"[SUCCESS] Re-ranked to top {len(results)} results")
        
        return results
    
    def get_statistics(self) -> Dict:
        """
        Get vector store statistics.
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            "persist_dir": self.persist_dir,
            "embedding_model": self.embedding_model,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "total_vectors": self.index.ntotal if self.index else 0,
            "index_dimension": self.index.d if self.index else 0,
            "metadata_count": len(self.metadata)
        }
        
        return stats


def build_vector_store_from_all_documents(data_dir: str = None,
                                         persist_dir: str = FAISS_STORE_DIR,
                                         use_extracted: bool = True) -> FaissVectorStore:
    """
    Convenience function to build vector store from all documents.
    
    Args:
        data_dir: Optional data directory (if None, uses EXTRACTED_DATA_DIR for categorized files)
        persist_dir: Directory to save vector store
        use_extracted: If True and data_dir is None, uses EXTRACTED_DATA_DIR with all 45 categorized files
        
    Returns:
        FaissVectorStore instance
    """
    print("="*60)
    print("COLLEGE AI - FAISS VECTOR STORE BUILDER")
    print("="*60)
    
    # Load documents from extracted categorized data by default
    if data_dir is None and use_extracted:
        data_dir = EXTRACTED_DATA_DIR
        print(f"\n[INFO] Using categorized data from: {data_dir}")
    
    # Load documents
    print("\n[STEP 1] Loading documents...")
    documents = load_all_documents(data_dir)
    
    if not documents:
        print("[ERROR] No documents loaded")
        return None
    
    print(f"[SUCCESS] Loaded {len(documents)} documents")
    
    # Show category breakdown
    categories = {}
    for doc in documents:
        cat = doc.metadata.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\n[INFO] Documents by category:")
    for cat, count in sorted(categories.items()):
        print(f"  • {cat}: {count} files")
    
    # Build vector store
    print("\n[STEP 2] Building vector store with semantic cleaning...")
    store = FaissVectorStore(persist_dir=persist_dir)
    store.build_from_documents(documents, clean_text=True)
    
    # Show statistics
    print("\n[STEP 3] Vector Store Statistics:")
    stats = store.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    return store


def build_vector_store_by_category(category: str,
                                   persist_dir: str = None) -> FaissVectorStore:
    """
    Build vector store for specific category.
    
    Args:
        category: Category name
        persist_dir: Optional persist directory
        
    Returns:
        FaissVectorStore instance
    """
    if persist_dir is None:
        persist_dir = f"{FAISS_STORE_DIR}_{category}"
    
    print("="*60)
    print(f"VECTOR STORE BUILDER - Category: {category}")
    print("="*60)
    
    # Load category documents
    print(f"\n[STEP 1] Loading '{category}' documents...")
    documents = load_documents_by_category(category)
    
    if not documents:
        print(f"[ERROR] No documents found for category '{category}'")
        return None
    
    # Build vector store
    print(f"\n[STEP 2] Building vector store for '{category}'...")
    store = FaissVectorStore(persist_dir=persist_dir)
    store.build_from_documents(documents)
    
    return store


# Example usage and testing
if __name__ == "__main__":
    print("="*60)
    print("EXAMPLE 1: Build vector store from ALL EXTRACTED documents")
    print("="*60)
    
    # Build from ALL 45 extracted categorized documents (not just sample.txt)
    store = build_vector_store_from_all_documents(use_extracted=True)
    
    if store:
        # Example queries with better semantic coverage
        print("\n" + "="*60)
        print("EXAMPLE 2: Test semantic search quality")
        print("="*60)
        
        queries = [
            "What are the placement statistics and top companies?",
            "Tell me about computer science department and CSE programs",
            "How to apply for admission and what are the eligibility criteria?",
            "What facilities are available on campus like library and hostel?",
            "Tell me about events, fests, and cultural activities"
        ]
        
        for query in queries:
            results = store.query(query, top_k=3)
            
            print(f"\n� Query: '{query}'")
            print(f"{'─'*60}")
            
            for i, result in enumerate(results, 1):
                meta = result['metadata']
                distance = result['distance']
                
                # Good matches should have distance < 1.0
                quality = "🟢 Excellent" if distance < 0.8 else "🟡 Good" if distance < 1.2 else "🔴 Weak"
                
                print(f"\n{i}. {quality} Match (Distance: {distance:.3f})")
                print(f"   📁 Category: {meta.get('category', 'N/A')}")
                print(f"   📄 File: {meta.get('filename', 'N/A')}")
                print(f"   📝 Text: {meta.get('text', '')[:200]}...")
        
        # Example 3: Test with re-ranker
        print("\n" + "="*60)
        print("EXAMPLE 3: Compare with and without re-ranker")
        print("="*60)
        
        test_query = "What are the placement statistics and average package?"
        
        # Without reranker
        print(f"\n🔍 Query (FAISS only): '{test_query}'")
        results_no_rerank = store.query(test_query, top_k=5, rerank=False)
        
        print("\n📊 FAISS Results:")
        for i, r in enumerate(results_no_rerank, 1):
            print(f"{i}. Distance: {r['distance']:.3f} | {r['metadata']['category']}")
            print(f"   {r['metadata']['text'][:100]}...")
        
        # With reranker
        print(f"\n🔍 Query (FAISS + Re-ranker): '{test_query}'")
        store.enable_reranker()  # Enable re-ranking
        results_reranked = store.query(test_query, top_k=5, rerank=True)
        
        print("\n✨ Re-ranked Results:")
        for i, r in enumerate(results_reranked, 1):
            rerank_score = r.get('rerank_score', 'N/A')
            score_str = f"{rerank_score:.4f}" if isinstance(rerank_score, float) else rerank_score
            print(f"{i}. Rerank: {score_str} | FAISS: {r['distance']:.3f} | {r['metadata']['category']}")
            print(f"   {r['metadata']['text'][:100]}...")
        
        # Example 4: Load existing store
        print("\n" + "="*60)
        print("EXAMPLE 4: Load existing vector store")
        print("="*60)
        
        new_store = FaissVectorStore()
        new_store.load()
        new_store.enable_reranker()  # Enable reranker on loaded store
        
        results = new_store.query("placement records and job opportunities", top_k=3)
        print(f"\n📊 Search results from loaded store:")
        for i, result in enumerate(results, 1):
            meta = result['metadata']
            rerank_score = result.get('rerank_score', 'N/A')
            score_str = f"{rerank_score:.4f}" if isinstance(rerank_score, float) else "N/A"
            print(f"\n{i}. Rerank: {score_str} | Distance: {result['distance']:.3f}")
            print(f"   Category: {meta.get('category', 'N/A')}")
            print(f"   Text: {meta.get('text', '')[:150]}...")
        
        print("\n" + "="*60)
        print("✅ Vector store is ready for production use!")
        print("="*60)
