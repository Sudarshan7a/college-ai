"""
RAG (Retrieval-Augmented Generation) Module for College AI
Combines vector search with LLM for intelligent Q&A.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Import the upgraded vector store (no duplication!)
from src.vector_store import FaissVectorStore, build_vector_store_from_all_documents
from src.config import BASE_PATH

# LangChain LLM imports
try:
    from langchain_groq import ChatGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("[WARNING] Groq not available. Install: pip install langchain-groq")

try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


# Load environment variables
load_dotenv()


class CollegeRAG:
    """
    RAG system for College AI Q&A.
    Uses upgraded FaissVectorStore with optional re-ranker.
    """
    
    def __init__(self, 
                 persist_dir: str = None,
                 embedding_model: str = None,
                 llm_provider: str = "groq",
                 llm_model: str = "gemma2-9b-it",
                 use_reranker: bool = True,
                 auto_build: bool = True):
        """
        Initialize RAG system.
        
        Args:
            persist_dir: FAISS store directory (default: data/faiss_store)
            embedding_model: Embedding model (default: MPNet from config)
            llm_provider: "groq", "openai", or "gemini"
            llm_model: Model name for the LLM
            use_reranker: Enable CrossEncoder re-ranking
            auto_build: Auto-build vector store if not exists
        """
        print("="*60)
        print("COLLEGE AI - RAG SYSTEM")
        print("="*60)
        
        # Use default paths if not specified
        if persist_dir is None:
            persist_dir = f"{BASE_PATH}/data/faiss_store"
        
        # Initialize vector store (uses upgraded version with MPNet)
        print(f"\n[STEP 1] Loading Vector Store...")
        if embedding_model:
            self.vectorstore = FaissVectorStore(
                persist_dir=persist_dir,
                embedding_model=embedding_model
            )
        else:
            # Uses default MPNet model from config
            self.vectorstore = FaissVectorStore(persist_dir=persist_dir)
        
        # Check if vector store exists
        faiss_path = os.path.join(persist_dir, "faiss.index")
        meta_path = os.path.join(persist_dir, "metadata.pkl")
        
        if not (os.path.exists(faiss_path) and os.path.exists(meta_path)):
            if auto_build:
                print("[INFO] Vector store not found. Building from documents...")
                store = build_vector_store_from_all_documents(
                    persist_dir=persist_dir,
                    use_extracted=True
                )
                self.vectorstore = store
            else:
                raise FileNotFoundError(
                    f"Vector store not found at {persist_dir}. "
                    "Run vector_store.py first or set auto_build=True"
                )
        else:
            print("[INFO] Loading existing vector store...")
            self.vectorstore.load()
        
        # Enable re-ranker for better accuracy
        if use_reranker:
            print("[INFO] Enabling re-ranker for improved accuracy...")
            try:
                self.vectorstore.enable_reranker()
            except Exception as e:
                print(f"[WARNING] Could not enable re-ranker: {e}")
        
        # Initialize LLM
        print(f"\n[STEP 2] Initializing LLM: {llm_provider} - {llm_model}")
        self.llm = self._init_llm(llm_provider, llm_model)
        
        print("\n[SUCCESS] RAG system ready!")
        print("="*60)
    
    def _init_llm(self, provider: str, model: str):
        """Initialize LLM based on provider."""
        if provider.lower() == "groq":
            if not GROQ_AVAILABLE:
                raise ImportError("Groq not available. Install: pip install langchain-groq")
            
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment variables")
            
            return ChatGroq(groq_api_key=api_key, model_name=model)
        
        elif provider.lower() == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError("OpenAI not available. Install: pip install langchain-openai")
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            
            return ChatOpenAI(api_key=api_key, model=model)
        
        elif provider.lower() == "gemini":
            if not GEMINI_AVAILABLE:
                raise ImportError("Gemini not available. Install: pip install langchain-google-genai")
            
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables")
            
            return ChatGoogleGenerativeAI(google_api_key=api_key, model=model)
        
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search vector store for relevant documents.
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            List of result dictionaries
        """
        return self.vectorstore.query(query, top_k=top_k)
    
    def get_context(self, query: str, top_k: int = 5) -> str:
        """
        Get concatenated context from top results.
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            Concatenated text from results
        """
        results = self.search(query, top_k=top_k)
        texts = [r["metadata"].get("text", "") for r in results if r.get("metadata")]
        return "\n\n".join(texts)
    
    def ask(self, query: str, top_k: int = 5, include_sources: bool = True) -> Dict[str, any]:
        """
        Ask a question and get LLM-generated answer with context.
        
        Args:
            query: User question
            top_k: Number of context documents to retrieve
            include_sources: Include source documents in response
            
        Returns:
            Dictionary with 'answer', 'sources', 'context'
        """
        print(f"\n[QUERY] {query}")
        
        # Retrieve relevant documents
        results = self.search(query, top_k=top_k)
        
        if not results:
            return {
                "answer": "I couldn't find any relevant information in the documents.",
                "sources": [],
                "context": ""
            }
        
        # Build context
        context_parts = []
        sources = []
        
        for i, r in enumerate(results, 1):
            meta = r.get("metadata", {})
            text = meta.get("text", "")
            category = meta.get("category", "unknown")
            filename = meta.get("filename", "unknown")
            
            context_parts.append(f"[Document {i}] {text}")
            sources.append({
                "index": i,
                "category": category,
                "filename": filename,
                "distance": r.get("distance", 0),
                "rerank_score": r.get("rerank_score"),
                "text_preview": text[:200] + "..." if len(text) > 200 else text
            })
        
        context = "\n\n".join(context_parts)
        
        # Create prompt
        prompt = self._create_prompt(query, context)
        
        # Get LLM response
        print("[INFO] Generating answer with LLM...")
        response = self.llm.invoke(prompt)
        answer = response.content if hasattr(response, 'content') else str(response)
        
        result = {
            "answer": answer,
            "context": context,
            "query": query
        }
        
        if include_sources:
            result["sources"] = sources
        
        return result
    
    def _create_prompt(self, query: str, context: str) -> str:
        """Create prompt for LLM."""
        prompt = f"""You are a helpful AI assistant for a college information system. 
Answer the user's question based ONLY on the provided context from the college documents.

If the context doesn't contain enough information to answer the question, say so clearly.
Be concise, accurate, and helpful.

Context from college documents:
{context}

User Question: {query}

Answer:"""
        
        return prompt
    
    def chat(self, query: str, top_k: int = 3) -> str:
        """
        Simple chat interface - returns just the answer.
        
        Args:
            query: User question
            top_k: Number of context documents
            
        Returns:
            Answer string
        """
        result = self.ask(query, top_k=top_k, include_sources=False)
        return result["answer"]


# Convenience function
def create_rag_system(llm_provider: str = "groq",
                     llm_model: str = "gemma2-9b-it",
                     use_reranker: bool = True) -> CollegeRAG:
    """
    Create RAG system with default settings.
    
    Args:
        llm_provider: "groq", "openai", or "gemini"
        llm_model: Model name
        use_reranker: Enable re-ranker
        
    Returns:
        CollegeRAG instance
    """
    return CollegeRAG(
        llm_provider=llm_provider,
        llm_model=llm_model,
        use_reranker=use_reranker
    )


# Example usage
if __name__ == "__main__":
    print("\n" + "="*60)
    print("EXAMPLE: RAG Q&A System")
    print("="*60)
    
    # Create RAG system (uses upgraded vector store with MPNet + re-ranker)
    rag = create_rag_system(
        llm_provider="groq",
        llm_model="gemma2-9b-it",
        use_reranker=True
    )
    
    # Example queries
    queries = [
        "What are the placement statistics?",
        "Tell me about the computer science department",
        "How do I apply for admission?",
        "What facilities are available on campus?"
    ]
    
    for query in queries:
        print("\n" + "─"*60)
        result = rag.ask(query, top_k=3)
        
        print(f"❓ Question: {query}")
        print(f"\n💡 Answer:\n{result['answer']}")
        
        if result.get('sources'):
            print(f"\n📚 Sources:")
            for src in result['sources']:
                rerank = f"Rerank: {src['rerank_score']:.3f}" if src['rerank_score'] else ""
                print(f"  • {src['category']}/{src['filename']} "
                      f"(Distance: {src['distance']:.3f}, {rerank})")
