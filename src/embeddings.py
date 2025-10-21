"""
Embeddings Generator for College AI
Creates vector embeddings from LangChain documents with chunking and vector storage.
"""

from pathlib import Path
from typing import List, Optional, Any
import sys
import os

# Suppress TensorFlow warnings
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import numpy as np

from src.data_loader import load_all_documents, load_documents_by_category
from src.config import BASE_PATH


# Configuration
VECTORSTORE_DIR = f"{BASE_PATH}/data/vectorstore"
# Upgraded to MPNet for better semantic understanding
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"  # Better semantic accuracy than MiniLM
CHUNK_SIZE = 2000  # Increased for better context retention
CHUNK_OVERLAP = 300  # More overlap for continuity


class EmbeddingPipeline:
    """
    Pipeline for chunking documents and creating embeddings.
    """
    
    def __init__(self, model_name: str = EMBEDDING_MODEL, 
                 chunk_size: int = CHUNK_SIZE, 
                 chunk_overlap: int = CHUNK_OVERLAP):
        """
        Initialize the embedding pipeline.
        
        Args:
            model_name: SentenceTransformer model name
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.model_name = model_name
        
        print(f"[INFO] Initializing embedding pipeline with model: {model_name}")
        self.model = SentenceTransformer(model_name)
        print(f"[INFO] Chunk size: {chunk_size}, Overlap: {chunk_overlap}")
        
        self.chunks = []
        self.embeddings = None
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into smaller chunks for better embedding quality.
        
        Args:
            documents: List of LangChain Document objects
            
        Returns:
            List of chunked Document objects
        """
        if not documents:
            raise ValueError("No documents provided for chunking")
        
        print(f"\n[INFO] Chunking {len(documents)} documents...")
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        self.chunks = splitter.split_documents(documents)
        print(f"[SUCCESS] Split {len(documents)} documents into {len(self.chunks)} chunks")
        
        return self.chunks
    
    def embed_chunks(self, chunks: Optional[List[Document]] = None) -> np.ndarray:
        """
        Generate embeddings for document chunks.
        
        Args:
            chunks: Optional list of chunks. If None, uses self.chunks
            
        Returns:
            Numpy array of embeddings
        """
        if chunks is None:
            chunks = self.chunks
        
        if not chunks:
            raise ValueError("No chunks provided. Call chunk_documents() first.")
        
        texts = [chunk.page_content for chunk in chunks]
        print(f"\n[INFO] Generating embeddings for {len(texts)} chunks...")
        
        self.embeddings = self.model.encode(
            texts, 
            show_progress_bar=True,
            normalize_embeddings=True
        )
        
        print(f"[SUCCESS] Generated embeddings with shape: {self.embeddings.shape}")
        return self.embeddings
    
    def get_embeddings(self) -> np.ndarray:
        """
        Get the generated embeddings.
        
        Returns:
            Numpy array of embeddings
        """
        if self.embeddings is None:
            raise ValueError("No embeddings generated. Call embed_chunks() first.")
        
        return self.embeddings
    
    def get_chunks(self) -> List[Document]:
        """
        Get the chunked documents.
        
        Returns:
            List of chunked Document objects
        """
        return self.chunks
    
    def get_statistics(self) -> dict:
        """
        Get statistics about embeddings.
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            "model": self.model_name,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "total_chunks": len(self.chunks) if self.chunks else 0,
            "embedding_dimensions": self.embeddings.shape[1] if self.embeddings is not None else 0,
            "total_embeddings": self.embeddings.shape[0] if self.embeddings is not None else 0
        }
        
        return stats


def create_embeddings_from_documents(documents: List[Document],
                                     model_name: str = EMBEDDING_MODEL,
                                     chunk_size: int = CHUNK_SIZE,
                                     chunk_overlap: int = CHUNK_OVERLAP) -> EmbeddingPipeline:
    """
    Create embeddings from provided documents.
    
    Args:
        documents: List of LangChain Document objects
        model_name: SentenceTransformer model name
        chunk_size: Size of text chunks
        chunk_overlap: Overlap between chunks
        
    Returns:
        EmbeddingPipeline instance with created embeddings
    """
    if not documents:
        raise ValueError("No documents provided")
    
    print(f"[INFO] Creating embeddings for {len(documents)} documents...")
    
    pipeline = EmbeddingPipeline(
        model_name=model_name,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    chunks = pipeline.chunk_documents(documents)
    embeddings = pipeline.embed_chunks(chunks)
    
    print(f"[SUCCESS] Created {len(chunks)} embeddings")
    
    return pipeline


# Example usage and testing
if __name__ == "__main__":
    print("="*60)
    print("COLLEGE AI - EMBEDDINGS GENERATOR")
    print("="*60)
    
    # Load documents
    print("\n[STEP 1] Loading documents...")
    docs = load_all_documents("data")
    
    if not docs:
        print("[ERROR] No documents loaded")
    else:
        print(f"[SUCCESS] Loaded {len(docs)} documents")
        
        # Create embeddings
        print("\n[STEP 2] Creating embeddings...")
        pipeline = create_embeddings_from_documents(docs)
        
        # Show statistics
        print("\n[STEP 3] Pipeline Statistics:")
        stats = pipeline.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Show example embedding
        embeddings = pipeline.get_embeddings()
        print(f"\n[INFO] Example embedding (first 10 values):")
        print(embeddings[0][:10] if len(embeddings) > 0 else None)
        
        print("\n[SUCCESS] Embeddings created successfully!")
        print("[INFO] Use vector_store.py to build searchable index")
