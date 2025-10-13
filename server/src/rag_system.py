"""
RAG (Retrieval-Augmented Generation) Module for College AI
Combines vector search with LLM for intelligent Q&A.
"""

import os
import re
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
from src.unanswered_logger import UnansweredQuestionLogger

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
                 persist_dir: Optional[str] = None,
                 embedding_model: Optional[str] = None,
                 llm_provider: str = "groq",
                 llm_model: str = "llama-3.3-70b-versatile",
                 use_reranker: bool = True,
                 auto_build: bool = True,
                 enable_logging: bool = True,
                 confidence_threshold: float = 0.6) -> None:
        """
        Initialize RAG system.
        
        Args:
            persist_dir: FAISS store directory (default: data/faiss_store)
            embedding_model: Embedding model (default: MPNet from config)
            llm_provider: "groq", "openai", or "gemini"
            llm_model: Model name for the LLM
            use_reranker: Enable CrossEncoder re-ranking
            auto_build: Auto-build vector store if not exists
            enable_logging: Enable logging of low-confidence questions
            confidence_threshold: Threshold below which questions are logged (0-1)
        """
        print("="*60)
        print("COLLEGE AI - RAG SYSTEM")
        print("="*60)
        
        # Use default paths if not specified
        if persist_dir is None:
            persist_dir = f"{BASE_PATH}/data/faiss_store"
        
        # Initialize unanswered question logger
        self.enable_logging = enable_logging
        self.confidence_threshold = confidence_threshold
        if enable_logging:
            self.logger: Optional[UnansweredQuestionLogger] = UnansweredQuestionLogger()
            print(f"[INFO] Unanswered question logging enabled (threshold: {confidence_threshold})")
        else:
            self.logger = None
        
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
        self.llm_provider = llm_provider
        self.model_name = llm_model
        self.llm = self._init_llm(llm_provider, llm_model)
        
        print("\n[SUCCESS] RAG system ready!")
        print("="*60)
    
    def _init_llm(self, provider: str, model: str) -> Any:
        """
        Initialize LLM based on provider.

        Args:
            provider: The LLM provider ('groq', 'openai', 'gemini')
            model: The specific model name to use

        Returns:
            The initialized LLM object (LangChain chat model)

        Raises:
            ImportError: If the required package is not installed
            ValueError: If the API key is missing or provider is unknown
        """
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
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search vector store for relevant documents.
        
        Args:
            query: Search query string
            top_k: Number of results to return
            
        Returns:
            List of result dictionaries containing metadata and distances
        """
        return self.vectorstore.query(query, top_k=top_k)
    
    def get_context(self, query: str, top_k: int = 5) -> str:
        """
        Get concatenated context from top results.
        
        Args:
            query: Search query string
            top_k: Number of results to use for context
            
        Returns:
            Concatenated text from results, separated by newlines
        """
        results = self.search(query, top_k=top_k)
        texts = [r["metadata"].get("text", "") for r in results if r.get("metadata")]
        return "\n\n".join(texts)
    
    def ask(self, query: str, top_k: int = 5, include_sources: bool = True, 
            session_id: Optional[str] = None, message_index: Optional[int] = None,
            message_id: Optional[str] = None) -> Dict[str, any]:
        """
        Ask a question and get LLM-generated answer with context.
        
        Args:
            query: User question
            top_k: Number of context documents to retrieve
            include_sources: Include source documents in response
            session_id: Session identifier for logging
            message_index: Position in conversation
            message_id: Frontend message ID for linking
            
        Returns:
            Dictionary with 'answer', 'sources', 'context', 'confidence_score'
        """
        print(f"\n[QUERY] {query}")
        
        # Retrieve relevant documents
        results = self.search(query, top_k=top_k)
        
        if not results:
            return self._handle_no_results(query, session_id, message_index, message_id)
        
        # Build context
        context, sources, doc_ids, categories, distances, rerank_scores = self._process_results(results)
        

        
        # Create prompt
        prompt = self._create_prompt(query, context)
        
        # Get LLM response
        print("[INFO] Generating answer with LLM...")
        response = self.llm.invoke(prompt)
        answer = response.content if hasattr(response, 'content') else str(response)
        
        # Calculate confidence score
        confidence_metrics = self._calculate_confidence(
            distances=distances,
            rerank_scores=rerank_scores,
            llm_response=answer
        )
        
        overall_confidence = confidence_metrics['overall_score']
        llm_uncertainty = confidence_metrics.get('llm_uncertainty_indicators', [])
        
        # Smart logging: Only log if LLM explicitly shows uncertainty
        # This filters out casual chit-chat like "hello" or "bye"
        should_log = False
        log_reason = None
        
        if self.enable_logging and self.logger:
            # Priority 1: LLM explicitly says it doesn't know (ALWAYS log)
            if llm_uncertainty and len(llm_uncertainty) > 0:
                should_log = True
                log_reason = "llm_explicit_uncertainty"
            # Priority 2: Very low confidence AND no results (likely off-topic)
            elif overall_confidence < -2.0 and len(results) < 2:
                should_log = True
                log_reason = "very_low_confidence_no_results"
            # Priority 3: Low confidence AND question is substantive (>10 chars, has question mark or keywords)
            elif overall_confidence < self.confidence_threshold:
                query_lower = query.lower()
                is_substantive = (
                    len(query) > 10 and
                    ('?' in query or 
                     any(word in query_lower for word in ['what', 'where', 'when', 'why', 'how', 'which', 'who', 'tell', 'explain', 'describe']))
                )
                if is_substantive:
                    should_log = True
                    log_reason = "low_confidence_substantive_question"
        
        if should_log:
            self.logger.log_question(
                query=query,
                model_response=answer,
                detection_source=log_reason,
                confidence_metrics=confidence_metrics,
                retrieval_context={
                    "num_docs_returned": len(results),
                    "top_doc_ids": doc_ids,
                    "query_embedding_similarities": [1 - d for d in distances],  # Convert distance to similarity
                    "categories": categories
                },
                session_id=session_id,
                message_index=message_index,
                message_id=message_id,
                model_version=f"{self.llm_provider}/{self.model_name}"
            )
            print(f"[UNANSWERED] {log_reason}: {query[:50]}...")
            print(f"[WARNING] Confidence: {overall_confidence:.2f}, Uncertainty indicators: {len(llm_uncertainty)} - Question logged")
        
        result = {
            "answer": answer,
            "context": context,
            "query": query,
            "confidence_score": overall_confidence
        }
        
        if include_sources:
            result["sources"] = sources
        
        return result
    
    def _handle_no_results(self, query: str, session_id: Optional[str], 
                          message_index: Optional[int], message_id: Optional[str]) -> Dict[str, Any]:
        """Handle case where no documents are found."""
        if self.enable_logging and self.logger:
            self.logger.log_question(
                query=query,
                model_response="I couldn't find any relevant information in the documents.",
                detection_source="auto_no_results",
                confidence_metrics={"overall_score": 0.0},
                retrieval_context={
                    "num_docs_returned": 0,
                    "top_doc_ids": [],
                    "query_embedding_similarities": [],
                    "categories": []
                },
                session_id=session_id,
                message_index=message_index,
                message_id=message_id,
                model_version=f"{self.llm_provider}/{self.model_name}"
            )
        
        return {
            "answer": "I couldn't find any relevant information in the documents.",
            "sources": [],
            "context": "",
            "confidence_score": 0.0
        }

    def _process_results(self, results: List[Dict[str, Any]]) -> tuple:
        """Process search results into context and metadata."""
        context_parts = []
        sources = []
        distances = []
        rerank_scores = []
        categories = []
        doc_ids = []
        
        for i, r in enumerate(results, 1):
            meta = r.get("metadata", {})
            text = meta.get("text", "")
            category = meta.get("category", "unknown")
            filename = meta.get("filename", "unknown")
            distance = r.get("distance", 0)
            rerank_score = r.get("rerank_score")
            
            context_parts.append(f"[Document {i}] {text}")
            sources.append({
                "index": i,
                "category": category,
                "filename": filename,
                "distance": distance,
                "rerank_score": rerank_score,
                "text_preview": text[:200] + "..." if len(text) > 200 else text,
                "text": text  # Full text for logging
            })
            
            distances.append(distance)
            if rerank_score is not None:
                rerank_scores.append(rerank_score)
            if category not in categories:
                categories.append(category)
            doc_ids.append(filename)
            
        context = "\n\n".join(context_parts)
        return context, sources, doc_ids, categories, distances, rerank_scores

    def _calculate_confidence(
        self,
        distances: List[float],
        rerank_scores: List[float],
        llm_response: str
    ) -> Dict[str, any]:
        """
        Calculate composite confidence score from multiple signals
        
        Args:
            distances: L2 distances from vector search (lower = better)
            rerank_scores: CrossEncoder scores (higher = better, 0-1 range)
            llm_response: The LLM's generated response
        
        Returns:
            Dict with overall_score and component scores
        """
        # 1. Vector similarity score (average of top-3, converted from distance)
        top_distances = distances[:3] if len(distances) >= 3 else distances
        # Convert L2 distance to similarity (0 = perfect match, higher = worse)
        # Normalize: assume distance range 0-2, convert to 0-1 similarity
        vector_similarities = [max(0, 1 - (d / 2)) for d in top_distances]
        avg_vector_sim = sum(vector_similarities) / len(vector_similarities) if vector_similarities else 0.0
        
        # 2. Reranker score (use best score if available)
        reranker_score = max(rerank_scores) if rerank_scores else None
        
        # 3. LLM certainty (detect hedging language)
        llm_certainty = self._detect_llm_certainty(llm_response)
        
        # Calculate weighted composite score
        if reranker_score is not None:
            # When reranker is available: 40% vector, 30% reranker, 30% LLM
            overall_score = (
                0.4 * avg_vector_sim +
                0.3 * reranker_score +
                0.3 * llm_certainty
            )
        else:
            # Without reranker: 60% vector, 40% LLM
            overall_score = (
                0.6 * avg_vector_sim +
                0.4 * llm_certainty
            )
        
        return {
            "overall_score": overall_score,
            "vector_similarity": avg_vector_sim,
            "reranker_score": reranker_score,
            "llm_uncertainty_indicators": self._extract_hedging_phrases(llm_response)
        }
    
    def _detect_llm_certainty(self, response: str) -> float:
        """
        Detect if LLM response contains uncertainty/hedging language
        
        Args:
            response: LLM's response text
        
        Returns:
            float: 1.0 if confident, 0.5 if hedging detected, 0.0 if explicit uncertainty
        """
        response_lower = response.lower()
        
        # Explicit uncertainty phrases (very low confidence)
        explicit_uncertainty = [
            "i don't have",
            "i don't know",
            "i'm not sure",
            "i cannot answer",
            "i'm unable to",
            "insufficient information",
            "not enough information",
            "doesn't contain enough",
            "i couldn't find"
        ]
        
        for phrase in explicit_uncertainty:
            if phrase in response_lower:
                return 0.0
        
        # Hedging phrases (moderate confidence)
        hedging = [
            "might be",
            "could be",
            "possibly",
            "perhaps",
            "it seems",
            "it appears",
            "may be",
            "unclear",
            "not clear"
        ]
        
        for phrase in hedging:
            if phrase in response_lower:
                return 0.5
        
        # No uncertainty detected (high confidence)
        return 1.0
    
    def _extract_hedging_phrases(self, response: str) -> List[str]:
        """Extract specific hedging/uncertainty phrases from response"""
        response_lower = response.lower()
        found_phrases = []
        
        all_phrases = [
            "I don't have",
            "I don't know",
            "I'm not sure",
            "I cannot answer",
            "insufficient information",
            "not enough information",
            "might be",
            "could be",
            "possibly",
            "perhaps",
            "it seems",
            "unclear"
        ]
        
        for phrase in all_phrases:
            if phrase.lower() in response_lower:
                found_phrases.append(phrase)
        
        return found_phrases
    
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
                     llm_model: str = "llama-3.3-70b-versatile",
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
        llm_model="llama-3.3-70b-versatile",
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
