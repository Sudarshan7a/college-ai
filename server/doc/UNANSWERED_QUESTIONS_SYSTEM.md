# Unanswered Questions Logging System - Implementation Plan

## Executive Summary

This document outlines the architecture and implementation of a feedback-loop subsystem designed to capture, analyze, and improve upon instances where our RAG (Retrieval-Augmented Generation) system delivers low-confidence or unsatisfactory responses. The system provides both automated confidence detection and explicit user feedback mechanisms, storing structured logs that enable continuous improvement of the knowledge base and retrieval algorithms.

---

## 1. Architecture Overview

### 1.1 System Components

The unanswered questions logging system comprises four primary modules that work in concert:

**Backend Detection Module** serves as the intelligent gatekeeping layer within the RAG pipeline. It evaluates each query-response cycle using multiple confidence signals: semantic similarity scores from the vector store, reranker confidence values, LLM response characteristics (hedging language, explicit uncertainty statements), and retrieval quality metrics. When confidence falls below configurable thresholds, the module triggers automatic logging without requiring user intervention.

**Persistence Layer** manages durable storage of question metadata using a hybrid approach. For rapid prototyping and moderate scale (up to ~100K records), we employ append-only JSONL files providing simplicity, version-control friendliness, and zero operational overhead. For production systems expecting higher volume or complex querying needs, PostgreSQL with JSONB columns offers ACID guarantees, efficient indexing, full-text search capabilities, and horizontal scalability. The dual-format support allows seamless migration as needs evolve.

**Admin API Module** exposes RESTful endpoints for internal teams to query, filter, and analyze logged questions. It provides time-series aggregations, confidence distribution analytics, topic clustering (using embedding similarity), and export functionality for deeper offline analysis. Authentication middleware (JWT-based or API key) restricts access to authorized personnel only.

**Frontend Feedback Interface** embeds non-intrusive feedback mechanisms directly into the chat experience. Users encounter thumbs-up/thumbs-down buttons beneath each assistant response, with optional free-text feedback for elaboration. The interface captures both explicit negative feedback and implicit signals (e.g., rapid follow-up questions suggesting initial response inadequacy). All feedback events trigger asynchronous logging calls to avoid blocking the user experience.

### 1.2 Technology Stack Rationale

**Storage Choice**: We begin with JSONL (JSON Lines) file storage because it offers immediate implementation without database setup, git-trackable logs for version control, and language-agnostic parsing. Each line is a self-contained JSON object, enabling streaming processing for large files. Transition to PostgreSQL occurs when query complexity demands relational joins or when write concurrency exceeds file-locking capabilities. PostgreSQL's JSONB type preserves schema flexibility while adding indexing and transaction support.

**API Framework**: FastAPI continues as our backend framework due to existing codebase integration, automatic OpenAPI documentation generation, and async/await support for non-blocking I/O operations during logging. Pydantic models enforce type safety and validation at API boundaries.

**Frontend Integration**: The chat widget uses React hooks for state management and Framer Motion for feedback UI animations. Feedback submission occurs via `fetch` API with optimistic UI updates (immediate visual confirmation) followed by background network calls. Failed submissions retry with exponential backoff to handle transient network issues.

---

## 2. Data Schema Specification

### 2.1 Core Schema Definition

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "UnansweredQuestionRecord",
  "type": "object",
  "required": ["id", "timestamp", "query", "detection_source"],
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique identifier for this log entry (UUID v4)"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp when question was logged (UTC)"
    },
    "user_anonymised_id": {
      "type": "string",
      "pattern": "^anon-[a-f0-9]{8}$",
      "description": "Anonymised user identifier (SHA256 hash prefix of session ID)"
    },
    "query": {
      "type": "string",
      "minLength": 1,
      "maxLength": 2000,
      "description": "The original user question/query text"
    },
    "model_response": {
      "type": "string",
      "description": "The LLM's generated response (may be truncated to 5000 chars)"
    },
    "confidence_metrics": {
      "type": "object",
      "properties": {
        "overall_score": {
          "type": "number",
          "minimum": 0,
          "maximum": 1,
          "description": "Composite confidence score (0 = no confidence, 1 = high confidence)"
        },
        "vector_similarity": {
          "type": "number",
          "minimum": 0,
          "maximum": 1,
          "description": "Average cosine similarity of top-k retrieved documents"
        },
        "reranker_score": {
          "type": "number",
          "minimum": 0,
          "maximum": 1,
          "description": "CrossEncoder reranking confidence for best match"
        },
        "llm_uncertainty_indicators": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Detected hedging phrases: ['I don't have enough information', 'I'm not sure']"
        }
      }
    },
    "retrieval_context_snapshot": {
      "type": "object",
      "properties": {
        "num_docs_returned": {
          "type": "integer",
          "minimum": 0,
          "description": "Total number of documents retrieved from vector store"
        },
        "top_doc_ids": {
          "type": "array",
          "items": {"type": "string"},
          "maxItems": 10,
          "description": "IDs of top-10 retrieved documents (for correlation analysis)"
        },
        "query_embedding_similarities": {
          "type": "array",
          "items": {
            "type": "number",
            "minimum": 0,
            "maximum": 1
          },
          "description": "Cosine similarity scores for each retrieved document"
        },
        "categories": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Document categories that matched (e.g., ['admissions', 'placements'])"
        }
      }
    },
    "detection_source": {
      "type": "string",
      "enum": ["auto_low_confidence", "user_negative_feedback", "auto_no_results", "user_escalation"],
      "description": "How this question was flagged as unanswered"
    },
    "user_feedback": {
      "type": "object",
      "properties": {
        "flagged_at": {
          "type": "string",
          "format": "date-time",
          "description": "When user submitted negative feedback"
        },
        "flag_reason": {
          "type": "string",
          "enum": ["incomplete", "incorrect", "irrelevant", "unclear", "other"],
          "description": "User-selected feedback category"
        },
        "free_text_feedback": {
          "type": "string",
          "maxLength": 1000,
          "description": "Optional free-form user comment"
        }
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "session_id": {
          "type": "string",
          "description": "Session identifier for conversation threading"
        },
        "message_index": {
          "type": "integer",
          "description": "Position of this Q&A in the conversation (1-indexed)"
        },
        "client_info": {
          "type": "object",
          "properties": {
            "user_agent": {"type": "string"},
            "ip_address_hash": {"type": "string"},
            "referrer": {"type": "string"}
          }
        },
        "model_version": {
          "type": "string",
          "description": "LLM model identifier (e.g., 'llama-3.3-70b-versatile@20250101')"
        }
      }
    },
    "resolution_status": {
      "type": "string",
      "enum": ["pending", "reviewed", "knowledge_base_updated", "wont_fix", "duplicate"],
      "default": "pending",
      "description": "Tracking field for admin workflow"
    },
    "admin_notes": {
      "type": "string",
      "maxLength": 2000,
      "description": "Internal notes from team reviewing this question"
    }
  }
}
```

### 2.2 Schema Design Rationale

The schema balances comprehensiveness with practical constraints. **Required fields** (`id`, `timestamp`, `query`, `detection_source`) ensure every log entry contains actionable data. **Confidence metrics** are decomposed into constituent signals rather than a single score, enabling post-hoc analysis of which factors correlate most strongly with user dissatisfaction. The **retrieval context snapshot** preserves enough information to reconstruct the RAG decision-making process without storing full document texts (which would balloon storage costs).

**User anonymization** follows privacy-by-design principles: we hash session IDs with SHA256 and store only the first 8 hex characters, providing sufficient uniqueness for session tracking while preventing re-identification. **Resolution status** fields transform the logging system from passive data collection into an active workflow management tool, enabling teams to track which unanswered questions have been addressed.

---

## 3. API Specification

### 3.1 Feedback Submission Endpoint

**POST** `/api/feedback`

```typescript
// Request Schema
interface FeedbackRequest {
  message_id: string;          // UUID of the message being rated
  query: string;               // Original user question
  response: string;            // Assistant's response (truncated to 5000 chars)
  helpful: boolean;            // true = thumbs up, false = thumbs down
  flag_reason?: 'incomplete' | 'incorrect' | 'irrelevant' | 'unclear' | 'other';
  free_text_feedback?: string; // Optional user comment (max 1000 chars)
  session_id?: string;         // Session identifier
  message_index?: number;      // Position in conversation
}

// Response Schema
interface FeedbackResponse {
  success: boolean;
  message_id: string;
  logged: boolean;             // false if thumbs-up (we only log negative feedback)
  log_entry_id?: string;       // UUID of created log entry (if logged)
}

// Example Request
POST /api/feedback
Content-Type: application/json

{
  "message_id": "msg-a1b2c3d4",
  "query": "What is the CSE department's placement record?",
  "response": "I don't have specific placement statistics for the CSE department.",
  "helpful": false,
  "flag_reason": "incomplete",
  "free_text_feedback": "I needed actual percentage numbers",
  "session_id": "sess-xyz789",
  "message_index": 3
}

// Example Response
{
  "success": true,
  "message_id": "msg-a1b2c3d4",
  "logged": true,
  "log_entry_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Endpoint Behavior**: When `helpful: false`, the system creates a new log entry with `detection_source: "user_negative_feedback"`. When `helpful: true`, we simply return success without logging (though in production, positive feedback could feed into a separate analytics pipeline for confidence calibration). The endpoint implements idempotency: submitting feedback for the same `message_id` multiple times updates the existing log entry rather than creating duplicates.

---

### 3.2 Admin Query Endpoint

**GET** `/api/admin/unanswered`

```typescript
// Query Parameters
interface QueryParams {
  limit?: number;                // Max results to return (default: 50, max: 500)
  offset?: number;               // Pagination offset (default: 0)
  min_confidence?: number;       // Filter: confidence_metrics.overall_score < this value
  max_confidence?: number;       // Filter: confidence_metrics.overall_score <= this value
  detection_source?: string;     // Filter: one of enum values
  date_from?: string;            // ISO 8601 date (inclusive)
  date_to?: string;              // ISO 8601 date (inclusive)
  resolution_status?: string;    // Filter by resolution status
  search?: string;               // Full-text search in query field
  sort_by?: 'timestamp' | 'confidence' | 'feedback_count';
  sort_order?: 'asc' | 'desc';   // Default: desc
}

// Response Schema
interface QueryResponse {
  success: boolean;
  total_count: number;           // Total matching records (for pagination)
  returned_count: number;        // Number of records in this response
  offset: number;
  questions: UnansweredQuestionRecord[];
  statistics: {
    avg_confidence: number;
    detection_source_breakdown: Record<string, number>;
    top_categories: Array<{category: string; count: number}>;
    resolution_status_breakdown: Record<string, number>;
  };
}

// Example Request
GET /api/admin/unanswered?limit=20&min_confidence=0&max_confidence=0.5&date_from=2025-10-01&sort_by=confidence

// Example Response
{
  "success": true,
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
      "detection_source": "auto_low_confidence",
      // ...additional fields
    },
    // ...19 more records
  ],
  "statistics": {
    "avg_confidence": 0.38,
    "detection_source_breakdown": {
      "auto_low_confidence": 82,
      "user_negative_feedback": 43,
      "auto_no_results": 22
    },
    "top_categories": [
      {"category": "admissions", "count": 34},
      {"category": "placements", "count": 28}
    ],
    "resolution_status_breakdown": {
      "pending": 120,
      "reviewed": 18,
      "knowledge_base_updated": 9
    }
  }
}
```

**Authentication**: This endpoint requires API key authentication via `X-API-Key` header or JWT bearer token. Unauthorized requests return `401 Unauthorized`. We implement rate limiting (100 requests/hour per API key) to prevent abuse.

---

### 3.3 Statistics Endpoint

**GET** `/api/admin/unanswered/stats`

```typescript
// Query Parameters (optional filters)
interface StatsParams {
  date_from?: string;
  date_to?: string;
  detection_source?: string;
}

// Response Schema
interface StatsResponse {
  success: boolean;
  date_range: {
    earliest_record: string;  // ISO 8601 timestamp
    latest_record: string;
    total_days: number;
  };
  totals: {
    all_time_count: number;
    last_7_days: number;
    last_30_days: number;
  };
  confidence_distribution: {
    bins: Array<{min: number; max: number; count: number}>;
    mean: number;
    median: number;
    std_dev: number;
  };
  temporal_trends: Array<{
    date: string;              // YYYY-MM-DD
    count: number;
    avg_confidence: number;
  }>;
  top_failing_queries: Array<{
    query_pattern: string;     // Clustering similar queries
    count: number;
    avg_confidence: number;
    example_query: string;
  }>;
}
```

This endpoint provides high-level analytics without returning individual records, making it suitable for dashboard visualizations. The **confidence distribution** uses 10 bins (0.0-0.1, 0.1-0.2, ..., 0.9-1.0) to reveal whether low-confidence questions cluster at specific thresholds. **Temporal trends** enable time-series charts showing whether answer quality improves as the knowledge base grows.

---

## 4. Frontend Feedback Mechanism

### 4.1 User Experience Flow

The feedback interaction follows a minimalist, non-intrusive design philosophy. Each assistant message in the chat interface displays two small icon buttons aligned to the bottom-right of the message bubble: a thumbs-up (👍) and thumbs-down (👎) rendered in muted gray. On hover, the icons brighten and scale slightly (10% zoom) using Framer Motion's `whileHover` animation, providing subtle affordance.

**Step 1 - Initial Feedback**: When a user clicks the thumbs-down button, the icon transforms to a filled red version with a brief haptic-like scale animation (scale: 0.9 → 1.1 → 1.0 over 300ms). Simultaneously, a compact feedback form slides down below the message using a smooth spring animation.

**Step 2 - Reason Selection**: The form presents five radio buttons with clear labels: "Incomplete answer," "Incorrect information," "Irrelevant response," "Answer unclear," and "Other." Below the radio buttons, a textarea appears for optional free-text feedback with placeholder text: "Help us improve—what would a better answer include? (optional)."

**Step 3 - Submission**: A "Submit Feedback" button appears enabled only after the user selects a reason. Clicking it triggers an optimistic UI update: the form collapses, the thumbs-down icon remains filled red (indicating feedback recorded), and a toast notification appears: "Thanks for your feedback! We'll work to improve this answer." The UI does not block or show loading spinners, maintaining conversational flow.

**Step 4 - Background Processing**: Asynchronously, the frontend sends a POST request to `/api/feedback`. If the request fails (network error, server timeout), the system retries up to three times with exponential backoff (1s, 2s, 4s delays). If all retries fail, the thumbs-down icon gains a small yellow dot indicator, and clicking it again shows the error: "Feedback couldn't be sent. Try again?" with a retry button.

**Thumbs-Up Interaction**: Clicking thumbs-up immediately fills the icon green and sends a single feedback ping (no form) to record positive sentiment. This helps calibrate confidence thresholds: if 80% of responses with confidence >0.7 receive thumbs-up, the threshold is well-tuned.

### 4.2 Frontend Implementation Pseudocode

```typescript
// In ChatWidget.tsx component
const [feedbackState, setFeedbackState] = useState<Record<string, FeedbackState>>({});

interface FeedbackState {
  status: 'idle' | 'form_open' | 'submitting' | 'submitted' | 'error';
  selected_reason?: string;
  free_text?: string;
  error_message?: string;
}

const handleFeedback = async (messageId: string, isPositive: boolean) => {
  if (isPositive) {
    // Immediate optimistic update
    setFeedbackState(prev => ({
      ...prev,
      [messageId]: { status: 'submitted' }
    }));
    
    // Background ping (fire-and-forget)
    await submitFeedback({ message_id: messageId, helpful: true, /* ... */ });
    return;
  }
  
  // Negative feedback: open form
  setFeedbackState(prev => ({
    ...prev,
    [messageId]: { status: 'form_open' }
  }));
};

const submitNegativeFeedback = async (messageId: string) => {
  const state = feedbackState[messageId];
  if (!state.selected_reason) return;
  
  setFeedbackState(prev => ({
    ...prev,
    [messageId]: { ...prev[messageId], status: 'submitting' }
  }));
  
  try {
    await submitFeedbackWithRetry({
      message_id: messageId,
      helpful: false,
      flag_reason: state.selected_reason,
      free_text_feedback: state.free_text,
      // ...other fields
    });
    
    setFeedbackState(prev => ({
      ...prev,
      [messageId]: { ...prev[messageId], status: 'submitted' }
    }));
    
    showToast('Thanks for your feedback!', 'success');
  } catch (error) {
    setFeedbackState(prev => ({
      ...prev,
      [messageId]: {
        ...prev[messageId],
        status: 'error',
        error_message: error.message
      }
    }));
  }
};

async function submitFeedbackWithRetry(data: FeedbackRequest, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      if (i === retries - 1) throw error;
      await delay(Math.pow(2, i) * 1000); // Exponential backoff
    }
  }
}
```

---

## 5. Backend Implementation Modules

### 5.1 Detection Logic

The confidence detection module operates as middleware in the RAG pipeline, evaluating responses immediately after LLM generation. It calculates a composite confidence score using weighted signals:

**Formula**: `confidence = 0.4 × vector_similarity + 0.3 × reranker_score + 0.3 × llm_certainty`

- **vector_similarity**: Average cosine similarity of top-3 retrieved documents (L2 normalized)
- **reranker_score**: CrossEncoder confidence for the best-matching document
- **llm_certainty**: Binary score (1.0 if no hedging phrases detected, 0.5 if hedging present)

Hedging detection uses a regex pattern matching common uncertainty markers: `/(I don't have|I'm not sure|I don't know|insufficient information|unable to answer)/i`.

When `confidence < 0.6` (configurable threshold), the system logs the question with `detection_source: "auto_low_confidence"`. If vector search returns zero results, it logs with `detection_source: "auto_no_results"`.

### 5.2 Storage Layer

```python
# server/src/unanswered_logger.py
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
import hashlib

class UnansweredQuestionLogger:
    """
    Manages persistence and querying of unanswered question logs.
    Supports both JSONL file storage and PostgreSQL backends.
    """
    
    def __init__(
        self,
        storage_backend: str = "jsonl",  # or "postgres"
        log_file_path: str = "data/logs/unanswered_questions.jsonl",
        db_connection_string: Optional[str] = None
    ):
        self.backend = storage_backend
        
        if storage_backend == "jsonl":
            self.log_file = Path(log_file_path)
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            if not self.log_file.exists():
                self.log_file.touch()
        elif storage_backend == "postgres":
            if not db_connection_string:
                raise ValueError("PostgreSQL backend requires db_connection_string")
            self.db = self._init_postgres_connection(db_connection_string)
            self._ensure_table_exists()
    
    def log_question(
        self,
        query: str,
        model_response: str,
        detection_source: str,
        confidence_metrics: Optional[Dict[str, Any]] = None,
        retrieval_context: Optional[Dict[str, Any]] = None,
        user_feedback: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        message_index: Optional[int] = None,
        model_version: Optional[str] = None
    ) -> str:
        """
        Create a new log entry.
        
        Returns:
            str: UUID of the created log entry
        """
        log_id = str(uuid.uuid4())
        anonymised_user_id = self._anonymise_session(session_id) if session_id else None
        
        record = {
            "id": log_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_anonymised_id": anonymised_user_id,
            "query": query,
            "model_response": model_response[:5000],  # Truncate
            "confidence_metrics": confidence_metrics or {},
            "retrieval_context_snapshot": retrieval_context or {},
            "detection_source": detection_source,
            "user_feedback": user_feedback,
            "metadata": {
                "session_id": anonymised_user_id,
                "message_index": message_index,
                "model_version": model_version
            },
            "resolution_status": "pending",
            "admin_notes": None
        }
        
        if self.backend == "jsonl":
            self._append_to_jsonl(record)
        elif self.backend == "postgres":
            self._insert_to_postgres(record)
        
        print(f"[LOGGED] {detection_source}: {query[:60]}...")
        return log_id
    
    def _anonymise_session(self, session_id: str) -> str:
        """Create anonymised user ID from session ID"""
        hash_obj = hashlib.sha256(session_id.encode())
        return f"anon-{hash_obj.hexdigest()[:8]}"
    
    def _append_to_jsonl(self, record: Dict) -> None:
        """Append record to JSONL file (atomic operation)"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record) + '\n')
    
    def query_logs(
        self,
        limit: int = 50,
        offset: int = 0,
        min_confidence: Optional[float] = None,
        max_confidence: Optional[float] = None,
        detection_source: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query log entries with filters.
        
        Returns:
            Dict with 'total_count', 'questions', and 'statistics'
        """
        if self.backend == "jsonl":
            return self._query_jsonl(
                limit, offset, min_confidence, max_confidence,
                detection_source, date_from, date_to, search
            )
        elif self.backend == "postgres":
            return self._query_postgres(
                limit, offset, min_confidence, max_confidence,
                detection_source, date_from, date_to, search
            )
    
    def _query_jsonl(self, limit, offset, min_conf, max_conf, source, date_from, date_to, search):
        """JSONL file-based query implementation"""
        questions = []
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                
                record = json.loads(line)
                
                # Apply filters
                if min_conf and record['confidence_metrics'].get('overall_score', 1.0) >= min_conf:
                    continue
                if max_conf and record['confidence_metrics'].get('overall_score', 0.0) > max_conf:
                    continue
                if source and record['detection_source'] != source:
                    continue
                if date_from and record['timestamp'] < date_from:
                    continue
                if date_to and record['timestamp'] > date_to:
                    continue
                if search and search.lower() not in record['query'].lower():
                    continue
                
                questions.append(record)
        
        # Sort by timestamp descending
        questions.sort(key=lambda x: x['timestamp'], reverse=True)
        
        total_count = len(questions)
        paginated = questions[offset:offset + limit]
        
        # Calculate statistics
        stats = self._calculate_statistics(questions)
        
        return {
            "total_count": total_count,
            "returned_count": len(paginated),
            "offset": offset,
            "questions": paginated,
            "statistics": stats
        }
    
    def _calculate_statistics(self, questions: List[Dict]) -> Dict:
        """Compute aggregate statistics"""
        if not questions:
            return {
                "avg_confidence": None,
                "detection_source_breakdown": {},
                "top_categories": [],
                "resolution_status_breakdown": {}
            }
        
        confidences = [
            q['confidence_metrics'].get('overall_score', 0)
            for q in questions
            if 'confidence_metrics' in q
        ]
        
        source_breakdown = {}
        for q in questions:
            src = q.get('detection_source', 'unknown')
            source_breakdown[src] = source_breakdown.get(src, 0) + 1
        
        # Category extraction from retrieval context
        category_counts = {}
        for q in questions:
            categories = q.get('retrieval_context_snapshot', {}).get('categories', [])
            for cat in categories:
                category_counts[cat] = category_counts.get(cat, 0) + 1
        
        top_categories = [
            {"category": cat, "count": count}
            for cat, count in sorted(category_counts.items(), key=lambda x: -x[1])[:5]
        ]
        
        resolution_breakdown = {}
        for q in questions:
            status = q.get('resolution_status', 'pending')
            resolution_breakdown[status] = resolution_breakdown.get(status, 0) + 1
        
        return {
            "avg_confidence": sum(confidences) / len(confidences) if confidences else None,
            "detection_source_breakdown": source_breakdown,
            "top_categories": top_categories,
            "resolution_status_breakdown": resolution_breakdown
        }
```

### 5.3 PostgreSQL Schema (Alternative Backend)

```sql
CREATE TABLE unanswered_questions (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_anonymised_id VARCHAR(16),
    query TEXT NOT NULL,
    model_response TEXT,
    confidence_metrics JSONB,
    retrieval_context_snapshot JSONB,
    detection_source VARCHAR(50) NOT NULL,
    user_feedback JSONB,
    metadata JSONB,
    resolution_status VARCHAR(30) DEFAULT 'pending',
    admin_notes TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_timestamp ON unanswered_questions(timestamp DESC);
CREATE INDEX idx_detection_source ON unanswered_questions(detection_source);
CREATE INDEX idx_resolution_status ON unanswered_questions(resolution_status);
CREATE INDEX idx_confidence ON unanswered_questions((confidence_metrics->>'overall_score'));
CREATE INDEX idx_query_search ON unanswered_questions USING gin(to_tsvector('english', query));

-- Trigger for updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_unanswered_questions_updated_at
    BEFORE UPDATE ON unanswered_questions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

---

## 6. Future Enhancements

### 6.1 Machine Learning Integration

As the log database grows beyond 1,000 entries, we can train supervised models to predict question answerability before expensive LLM calls. Features include query length, vocabulary overlap with knowledge base, named entity density, and historical confidence scores for similar questions. A lightweight logistic regression classifier (scikit-learn) can gate the RAG pipeline, returning a canned "I don't have information about that" response for questions predicted with >90% probability to fail.

### 6.2 Clustering and Topic Modeling

Apply HDBSCAN clustering on query embeddings (using the same MPNet model from the RAG pipeline) to identify themes in unanswered questions. For example, if 20 questions cluster around "hostel facilities," this signals a gap in the knowledge base requiring new document ingestion. Cluster labels generated via LLM-based summarization (prompt: "Summarize the common theme in these questions: ...") provide human-readable category names for admin dashboards.

### 6.3 Active Learning Loop

Implement a weekly batch process that:
1. Selects top 10 high-frequency unanswered questions (by cluster size)
2. Generates candidate answers using web search augmentation (e.g., searching the college's official website)
3. Presents draft answers to admins for review
4. On approval, automatically adds new documents to the vector store and reindexes

This transforms passive logging into active knowledge base expansion, reducing unanswered question volume by ~30-50% over 3 months (estimated based on similar systems).

### 6.4 Real-Time Alerting

Integrate with Slack/Discord webhooks to notify the team when:
- Daily unanswered question count exceeds 2× rolling 7-day average (anomaly detection)
- A question receives >5 negative feedbacks within 1 hour (viral misinformation risk)
- Average confidence drops below 0.5 for >10 consecutive questions (system degradation alert)

Alerts include clickable links to the admin dashboard filtered by the relevant criteria.

### 6.5 A/B Testing Framework

Extend the logging schema to include `experiment_group` field, enabling controlled experiments on confidence threshold tuning, retrieval algorithm changes, or LLM prompt variations. For instance, route 10% of traffic to a modified RAG pipeline with increased `top_k` parameter, then compare confidence distributions and user feedback rates between control and treatment groups using statistical significance tests (χ² test for categorical feedback, t-test for continuous confidence scores).

---

## 7. Implementation Checklist

### Phase 1: Foundation (Week 1)
- [ ] Create `server/src/unanswered_logger.py` with JSONL backend
- [ ] Implement confidence calculation in `server/src/rag_system.py`
- [ ] Add `/api/feedback` endpoint in `server/server.py`
- [ ] Create Pydantic models for request/response validation
- [ ] Write unit tests for logger (mock file I/O)

### Phase 2: Admin Interface (Week 2)
- [ ] Implement `/api/admin/unanswered` query endpoint
- [ ] Add `/api/admin/unanswered/stats` statistics endpoint
- [ ] Create API key authentication middleware
- [ ] Build admin dashboard React component
- [ ] Add data export functionality (CSV download)

### Phase 3: Frontend Integration (Week 3)
- [ ] Add thumbs-up/down buttons to `ChatWidget.tsx`
- [ ] Implement feedback form with reason selection
- [ ] Add retry logic with exponential backoff
- [ ] Create toast notification component
- [ ] Test offline/degraded network scenarios

### Phase 4: Production Hardening (Week 4)
- [ ] Migrate to PostgreSQL backend for production
- [ ] Add database migrations (Alembic or raw SQL)
- [ ] Implement log rotation for JSONL files (compress after 100MB)
- [ ] Set up monitoring (Prometheus metrics for log write rate)
- [ ] Create runbook for common admin tasks

---

## 8. Success Metrics

After 30 days of production operation, evaluate:

1. **Coverage**: % of low-confidence questions (<0.6) successfully logged (target: >95%)
2. **User Engagement**: % of responses receiving any feedback (target: >15%)
3. **Actionability**: % of logged questions reviewed by admins (target: >60%)
4. **Knowledge Base Growth**: # of new documents added from unanswered question analysis (target: >20)
5. **Confidence Trend**: Average confidence score improvement month-over-month (target: +5 percentage points)

## Conclusion

This unanswered questions logging system transforms the RAG pipeline from a static query-response mechanism into a continuously improving feedback loop. By capturing both automated confidence signals and explicit user feedback, we create a rich dataset for knowledge base expansion, retrieval algorithm tuning, and user experience enhancement. The modular architecture supports gradual scaling from file-based prototyping to database-backed production systems, while the admin API and dashboard enable data-driven decision-making. Future machine learning integrations will automate gap detection and answer generation, reducing manual review burden and accelerating the system's evolution toward comprehensive college information coverage.
