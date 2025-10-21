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
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the placement statistics?",
                "top_k": 3,
                "include_sources": True
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
