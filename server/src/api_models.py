"""
API Request/Response Models for College AI Backend
Pydantic models for type validation and API documentation
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for query endpoint"""
    query: str = Field(..., description="The question to ask", min_length=1)
    top_k: int = Field(default=3, description="Number of results to return", ge=1, le=10)
    include_sources: bool = Field(default=True, description="Include source documents in response")
    session_id: Optional[str] = Field(None, description="Session identifier for logging")
    message_index: Optional[int] = Field(None, description="Message position in conversation")
    message_id: Optional[str] = Field(None, description="Frontend message ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the placement statistics?",
                "top_k": 3,
                "include_sources": True,
                "session_id": "sess-abc123",
                "message_index": 1,
                "message_id": "msg-xyz789"
            }
        }


class Source(BaseModel):
    """Source document metadata"""
    category: str = Field(..., description="Document category")
    filename: str = Field(..., description="Source filename")
    text: str = Field(..., description="Relevant text snippet")
    distance: float = Field(..., description="Similarity distance (lower is better)")
    rerank_score: Optional[float] = Field(None, description="Re-ranking score (higher is better)")


class QueryResponse(BaseModel):
    """Response model for query endpoint"""
    answer: str = Field(..., description="Generated answer")
    query: str = Field(..., description="Original query")
    sources: List[Source] = Field(default_factory=list, description="Source documents used")
    processing_time: float = Field(..., description="Processing time in seconds")
    model_used: str = Field(default="llama-3.3-70b-versatile", description="LLM model used")
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "The Computer Science Department has excellent placement statistics...",
                "query": "What are the placement statistics?",
                "sources": [
                    {
                        "category": "placements",
                        "filename": "placement-statistics.txt",
                        "text": "Computer Science Department had 95% placement...",
                        "distance": 0.753,
                        "rerank_score": 0.921
                    }
                ],
                "processing_time": 1.234,
                "model_used": "llama-3.3-70b-versatile"
            }
        }


class SearchRequest(BaseModel):
    """Request model for search endpoint (no LLM, just vector search)"""
    query: str = Field(..., description="Search query", min_length=1)
    top_k: int = Field(default=5, description="Number of results to return", ge=1, le=20)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "computer science courses",
                "top_k": 5
            }
        }


class SearchResponse(BaseModel):
    """Response model for search endpoint"""
    query: str = Field(..., description="Original query")
    results: List[Source] = Field(..., description="Search results")
    processing_time: float = Field(..., description="Processing time in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "computer science courses",
                "results": [
                    {
                        "category": "departments",
                        "filename": "cse-courses.txt",
                        "text": "The CSE department offers courses in...",
                        "distance": 0.621,
                        "rerank_score": 0.887
                    }
                ],
                "processing_time": 0.123
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check endpoint"""
    status: str = Field(..., description="Server status (healthy/unhealthy)")
    models_loaded: bool = Field(..., description="Whether AI models are loaded")
    uptime_seconds: float = Field(..., description="Server uptime in seconds")
    vector_store_ready: bool = Field(..., description="Whether vector store is ready")
    llm_ready: bool = Field(..., description="Whether LLM is ready")
    total_vectors: Optional[int] = Field(None, description="Total vectors in store")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "models_loaded": True,
                "uptime_seconds": 123.45,
                "vector_store_ready": True,
                "llm_ready": True,
                "total_vectors": 143
            }
        }


class StatsResponse(BaseModel):
    """Response model for statistics endpoint"""
    total_queries: int = Field(..., description="Total queries processed")
    avg_response_time: float = Field(..., description="Average response time in seconds")
    uptime_seconds: float = Field(..., description="Server uptime in seconds")
    vector_store_info: Dict[str, Any] = Field(..., description="Vector store information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_queries": 42,
                "avg_response_time": 1.234,
                "uptime_seconds": 3600.5,
                "vector_store_info": {
                    "total_vectors": 143,
                    "dimension": 768,
                    "model": "sentence-transformers/all-mpnet-base-v2"
                }
            }
        }


class ErrorResponse(BaseModel):
    """Response model for errors"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Query processing failed",
                "detail": "LLM service temporarily unavailable"
            }
        }


# --- Feedback and Unanswered Questions Models ---

class FeedbackRequest(BaseModel):
    """Request model for user feedback submission"""
    message_id: str = Field(..., description="UUID of the message being rated")
    query: str = Field(..., description="Original user question")
    response: str = Field(..., description="Assistant's response", max_length=5000)
    helpful: bool = Field(..., description="True for thumbs up, False for thumbs down")
    flag_reason: Optional[str] = Field(
        None, 
        description="Reason for negative feedback",
        pattern="^(incomplete|incorrect|irrelevant|unclear|other)$"
    )
    free_text_feedback: Optional[str] = Field(
        None,
        description="Optional free-form user comment",
        max_length=1000
    )
    session_id: Optional[str] = Field(None, description="Session identifier")
    message_index: Optional[int] = Field(None, description="Position in conversation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg-a1b2c3d4",
                "query": "What is the CSE department's placement record?",
                "response": "I don't have specific placement statistics for the CSE department.",
                "helpful": False,
                "flag_reason": "incomplete",
                "free_text_feedback": "I needed actual percentage numbers",
                "session_id": "sess-xyz789",
                "message_index": 3
            }
        }


class FeedbackResponse(BaseModel):
    """Response model for feedback submission"""
    success: bool = Field(..., description="Whether feedback was recorded")
    message_id: str = Field(..., description="Message ID that was rated")
    logged: bool = Field(..., description="Whether question was logged (false for positive feedback)")
    log_entry_id: Optional[str] = Field(None, description="UUID of created log entry (if logged)")
    message: str = Field(default="Thank you for your feedback", description="Response message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message_id": "msg-a1b2c3d4",
                "logged": True,
                "log_entry_id": "550e8400-e29b-41d4-a716-446655440000",
                "message": "Thank you for your feedback"
            }
        }


class UnansweredQuestion(BaseModel):
    """Model for an unanswered question log entry"""
    id: str = Field(..., description="UUID of log entry")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    user_anonymised_id: Optional[str] = Field(None, description="Anonymised user ID")
    query: str = Field(..., description="The user's question")
    model_response: str = Field(..., description="The LLM's response")
    confidence_metrics: Dict[str, Any] = Field(..., description="Confidence scores")
    retrieval_context_snapshot: Dict[str, Any] = Field(..., description="Retrieval context")
    detection_source: str = Field(..., description="How question was flagged")
    user_feedback: Optional[Dict[str, Any]] = Field(None, description="User feedback data")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")
    resolution_status: str = Field(default="pending", description="Resolution status")
    admin_notes: Optional[str] = Field(None, description="Internal notes")


class UnansweredQuestionsResponse(BaseModel):
    """Response model for admin unanswered questions endpoint"""
    success: bool = Field(..., description="Whether request was successful")
    total_count: int = Field(..., description="Total matching records")
    returned_count: int = Field(..., description="Number of records in this response")
    offset: int = Field(..., description="Pagination offset")
    questions: List[Dict[str, Any]] = Field(..., description="List of unanswered questions")
    statistics: Dict[str, Any] = Field(..., description="Aggregate statistics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "total_count": 147,
                "returned_count": 20,
                "offset": 0,
                "questions": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "timestamp": "2025-10-22T15:34:21Z",
                        "query": "Who won the cricket World Cup in 1999?",
                        "confidence_metrics": {
                            "overall_score": 0.32,
                            "vector_similarity": 0.45,
                            "reranker_score": 0.28
                        },
                        "detection_source": "auto_low_confidence"
                    }
                ],
                "statistics": {
                    "avg_confidence": 0.38,
                    "detection_source_breakdown": {
                        "auto_low_confidence": 82,
                        "user_negative_feedback": 43,
                        "auto_no_results": 22
                    }
                }
            }
        }


class UnansweredStatsResponse(BaseModel):
    """Response model for admin statistics endpoint"""
    success: bool = Field(..., description="Whether request was successful")
    statistics: Dict[str, Any] = Field(..., description="Detailed statistics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "statistics": {
                    "date_range": {
                        "earliest_record": "2025-10-01T10:00:00Z",
                        "latest_record": "2025-10-22T15:34:21Z",
                        "total_days": 21
                    },
                    "totals": {
                        "all_time_count": 147,
                        "last_7_days": 23,
                        "last_30_days": 147
                    },
                    "confidence_distribution": {
                        "bins": [
                            {"min": 0.0, "max": 0.1, "count": 5},
                            {"min": 0.1, "max": 0.2, "count": 12}
                        ],
                        "mean": 0.38,
                        "median": 0.35
                    }
                }
            }
        }
