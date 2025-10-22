"""
College AI - FastAPI Backend Server
Pre-loads RAG system on startup for fast query responses
"""
import os
# Suppress TensorFlow warnings before importing other modules
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import time
import asyncio
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from src.rag_system import CollegeRAG
from src.api_models import (
    QueryRequest, QueryResponse, SearchRequest, SearchResponse,
    HealthResponse, StatsResponse, ErrorResponse, Source,
    FeedbackRequest, FeedbackResponse,
    UnansweredQuestionsResponse, UnansweredStatsResponse
)

# Global variables
rag_system: Optional[CollegeRAG] = None
server_start_time: float = 0
query_count: int = 0
total_response_time: float = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global rag_system, server_start_time
    
    print("=" * 60)
    print("🚀 COLLEGE AI BACKEND - STARTING UP")
    print("=" * 60)
    
    try:
        print("\n[1/3] Loading RAG system...")
        print("  ⏳ Loading vector store...")
        print("  ⏳ Loading re-ranker...")
        print("  ⏳ Initializing LLM...")
        
        rag_system = CollegeRAG(use_reranker=True)
        
        # Verify RAG system loaded correctly
        if rag_system is None:
            raise Exception("RAG system initialization returned None")
        
        if not hasattr(rag_system, 'vectorstore') or rag_system.vectorstore is None:
            raise Exception("Vector store not initialized properly")
        
        if not hasattr(rag_system.vectorstore, 'index') or rag_system.vectorstore.index is None:
            raise Exception("FAISS index not loaded - vector store may be empty or corrupted")
        
        print("\n✅ RAG system loaded successfully!")
        total_vecs = rag_system.vectorstore.total_vectors
        print(f"  📊 Vector Store: {total_vecs} vectors")
        print(f"  🎯 Re-ranker: {'Enabled' if hasattr(rag_system.vectorstore, 'reranker') and rag_system.vectorstore.reranker else 'Disabled'}")
        print(f"  🤖 LLM: {rag_system.model_name}")
        
        server_start_time = time.time()
        
        print("\n" + "=" * 60)
        print("✅ SERVER READY FOR REQUESTS!")
        print("=" * 60)
        print(f"📡 API Docs: http://localhost:8000/docs")
        print(f"🔍 Health Check: http://localhost:8000/api/health")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: Failed to load RAG system")
        print(f"   {str(e)}")
        print("\n⚠️  Server will start but queries will fail.")
        print("=" * 60 + "\n")
    
    yield
    
    # Shutdown
    print("\n🛑 Shutting down server...")


app = FastAPI(
    title="College AI Backend API",
    description="FastAPI backend for College AI chatbot with pre-loaded RAG system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - allow frontend to make requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "College AI Backend API",
        "status": "running",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.post("/api/query", 
          response_model=QueryResponse,
          tags=["Query"],
          summary="Ask a question using RAG")
async def query_endpoint(request: QueryRequest):
    """
    Ask a question about the college using RAG (Retrieval-Augmented Generation).
    
    The system will:
    1. Search the vector store for relevant documents
    2. Re-rank results for better accuracy
    3. Generate an answer using the LLM
    4. Return the answer with source citations
    
    **Processing time:** ~1-2 seconds
    """
    global rag_system, query_count, total_response_time
    
    if rag_system is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG system not loaded. Please wait for startup to complete."
        )
    
    try:
        start_time = time.time()
        
        # Run the query (async wrapper for sync function)
        result = await asyncio.to_thread(
            rag_system.ask,
            query=request.query,
            top_k=request.top_k,
            include_sources=request.include_sources,
            session_id=request.session_id,
            message_index=request.message_index,
            message_id=request.message_id
        )
        
        processing_time = time.time() - start_time
        
        # Update stats
        query_count += 1
        total_response_time += processing_time
        
        # Convert sources to Pydantic models
        sources = [
            Source(
                category=src.get("category", "unknown"),
                filename=src.get("filename", "unknown"),
                text=src.get("text", ""),
                distance=src.get("distance", 0.0),
                rerank_score=src.get("rerank_score")
            )
            for src in result.get("sources", [])
        ]
        
        return QueryResponse(
            answer=result["answer"],
            query=result["query"],
            sources=sources,
            processing_time=processing_time,
            model_used=rag_system.model_name
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing failed: {str(e)}"
        )


@app.post("/api/search",
          response_model=SearchResponse,
          tags=["Search"],
          summary="Vector search without LLM")
async def search_endpoint(request: SearchRequest):
    """
    Search for relevant documents without generating an answer.
    
    This is faster than /api/query since it only does vector search + re-ranking,
    without calling the LLM.
    
    **Processing time:** ~0.1-0.3 seconds
    """
    global rag_system
    
    if rag_system is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG system not loaded. Please wait for startup to complete."
        )
    
    try:
        start_time = time.time()
        
        # Run search (async wrapper for sync function)
        results = await asyncio.to_thread(
            rag_system.search,
            query=request.query,
            top_k=request.top_k
        )
        
        processing_time = time.time() - start_time
        
        # Convert to Pydantic models
        sources = [
            Source(
                category=result.get("category", "unknown"),
                filename=result.get("filename", "unknown"),
                text=result.get("text", ""),
                distance=result.get("distance", 0.0),
                rerank_score=result.get("rerank_score")
            )
            for result in results
        ]
        
        return SearchResponse(
            query=request.query,
            results=sources,
            processing_time=processing_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@app.get("/api/health",
         response_model=HealthResponse,
         tags=["Health"],
         summary="Check server health")
async def health_check():
    """
    Check if the server is healthy and models are loaded.
    
    Returns:
    - Server status
    - Whether models are loaded
    - Uptime
    - Vector store status
    - LLM status
    """
    global rag_system, server_start_time
    
    uptime = time.time() - server_start_time if server_start_time > 0 else 0
    
    models_loaded = rag_system is not None
    vector_store_ready = False
    llm_ready = False
    total_vectors = None
    
    if rag_system:
        try:
            vector_store_ready = rag_system.vectorstore is not None
            llm_ready = rag_system.llm is not None
            if vector_store_ready:
                total_vectors = rag_system.vectorstore.total_vectors
        except Exception:
            pass
    
    status_text = "healthy" if (models_loaded and vector_store_ready and llm_ready) else "unhealthy"
    
    return HealthResponse(
        status=status_text,
        models_loaded=models_loaded,
        uptime_seconds=uptime,
        vector_store_ready=vector_store_ready,
        llm_ready=llm_ready,
        total_vectors=total_vectors
    )


@app.get("/api/stats",
         response_model=StatsResponse,
         tags=["Stats"],
         summary="Get server statistics")
async def stats_endpoint():
    """
    Get server statistics including:
    - Total queries processed
    - Average response time
    - Uptime
    - Vector store info
    """
    global rag_system, server_start_time, query_count, total_response_time
    
    uptime = time.time() - server_start_time if server_start_time > 0 else 0
    avg_response_time = total_response_time / query_count if query_count > 0 else 0.0
    
    vector_store_info = {}
    if rag_system and rag_system.vectorstore:
        vector_store_info = {
            "total_vectors": rag_system.vectorstore.total_vectors,
            "dimension": rag_system.vectorstore.dimension,
            "model": rag_system.vectorstore.embedding_model,
            "reranker_enabled": rag_system.vectorstore.reranker is not None
        }
    
    return StatsResponse(
        total_queries=query_count,
        avg_response_time=avg_response_time,
        uptime_seconds=uptime,
        vector_store_info=vector_store_info
    )


@app.post("/api/feedback",
          response_model=FeedbackResponse,
          tags=["Feedback"],
          summary="Submit user feedback on responses")
async def feedback_endpoint(request: FeedbackRequest):
    """
    Submit user feedback on assistant responses.
    
    - Positive feedback (helpful=true): Simply recorded, not logged
    - Negative feedback (helpful=false): Logged as unanswered question with user feedback
    
    This enables continuous improvement of the system by tracking
    which responses users found unhelpful.
    """
    global rag_system
    
    if rag_system is None or not rag_system.enable_logging:
        return FeedbackResponse(
            success=True,
            message_id=request.message_id,
            logged=False,
            message="Feedback received (logging disabled)"
        )
    
    # Only log negative feedback
    if not request.helpful:
        try:
            # Log the question with user feedback
            log_id = rag_system.logger.log_question(
                query=request.query,
                model_response=request.response,
                detection_source="user_negative_feedback",
                user_feedback={
                    "flagged_at": time.time(),
                    "flag_reason": request.flag_reason or "not_helpful",
                    "free_text_feedback": request.free_text_feedback
                },
                session_id=request.session_id,
                message_index=request.message_index,
                message_id=request.message_id,
                model_version=f"{rag_system.llm_provider}/{rag_system.model_name}"
            )
            
            return FeedbackResponse(
                success=True,
                message_id=request.message_id,
                logged=True,
                log_entry_id=log_id,
                message="Thank you for your feedback! We'll work to improve this answer."
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to log feedback: {str(e)}"
            )
    else:
        # Positive feedback - just acknowledge
        return FeedbackResponse(
            success=True,
            message_id=request.message_id,
            logged=False,
            message="Thank you for your feedback!"
        )


@app.get("/api/admin/unanswered",
         response_model=UnansweredQuestionsResponse,
         tags=["Admin"],
         summary="Get unanswered questions (Admin only)")
async def get_unanswered_questions(
    limit: int = 50,
    offset: int = 0,
    min_confidence: Optional[float] = None,
    max_confidence: Optional[float] = None,
    detection_source: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    resolution_status: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "timestamp",
    sort_order: str = "desc"
):
    """
    Retrieve logged unanswered or low-confidence questions.
    
    **Query Parameters:**
    - `limit`: Maximum number of results (default: 50, max: 500)
    - `offset`: Pagination offset
    - `min_confidence`: Filter for confidence >= this value
    - `max_confidence`: Filter for confidence < this value  
    - `detection_source`: Filter by source (auto_low_confidence, user_negative_feedback, etc.)
    - `date_from`: Filter for dates >= this (ISO 8601)
    - `date_to`: Filter for dates <= this (ISO 8601)
    - `resolution_status`: Filter by status (pending, reviewed, etc.)
    - `search`: Full-text search in query field
    - `sort_by`: Field to sort by (timestamp or confidence)
    - `sort_order`: Sort direction (asc or desc)
    
    **Note:** This endpoint should be protected with authentication in production.
    For now, it's open for development purposes.
    """
    global rag_system
    
    if rag_system is None or not rag_system.enable_logging or not rag_system.logger:
        return UnansweredQuestionsResponse(
            success=False,
            total_count=0,
            returned_count=0,
            offset=offset,
            questions=[],
            statistics={}
        )
    
    try:
        # Limit maximum results to prevent abuse
        limit = min(limit, 500)
        
        result = rag_system.logger.query_logs(
            limit=limit,
            offset=offset,
            min_confidence=min_confidence,
            max_confidence=max_confidence,
            detection_source=detection_source,
            date_from=date_from,
            date_to=date_to,
            resolution_status=resolution_status,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return UnansweredQuestionsResponse(
            success=True,
            total_count=result['total_count'],
            returned_count=result['returned_count'],
            offset=result['offset'],
            questions=result['questions'],
            statistics=result['statistics']
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query logs: {str(e)}"
        )


@app.get("/api/admin/unanswered/stats",
         response_model=UnansweredStatsResponse,
         tags=["Admin"],
         summary="Get unanswered questions statistics")
async def get_unanswered_stats(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    """
    Get high-level statistics about unanswered questions.
    
    Returns time-series trends, confidence distributions, and top failing queries.
    Useful for dashboard visualizations.
    
    **Query Parameters:**
    - `date_from`: Filter for dates >= this (ISO 8601)
    - `date_to`: Filter for dates <= this (ISO 8601)
    """
    global rag_system
    
    if rag_system is None or not rag_system.enable_logging or not rag_system.logger:
        return UnansweredStatsResponse(
            success=False,
            statistics={}
        )
    
    try:
        stats = rag_system.logger.get_statistics(
            date_from=date_from,
            date_to=date_to
        )
        
        return UnansweredStatsResponse(
            success=True,
            statistics=stats
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes (disable in production)
        log_level="info"
    )
