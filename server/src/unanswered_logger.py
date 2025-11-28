"""
Unanswered Questions Logging System
Captures and persists questions that the RAG system couldn't answer with sufficient confidence
"""
import json
import uuid
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any, Literal

# Configure logging
logger = logging.getLogger(__name__)

class UnansweredQuestionLogger:
    """
    Manages persistence and querying of unanswered question logs.
    Supports JSONL file storage with future PostgreSQL backend support.
    """
    
    def __init__(
        self,
        storage_backend: Literal["jsonl", "postgres"] = "jsonl",
        log_file_path: str = "data/logs/unanswered_questions.jsonl",
        db_connection_string: Optional[str] = None
    ):
        """
        Initialize the logger
        
        Args:
            storage_backend: Storage type ('jsonl' or 'postgres')
            log_file_path: Path to JSONL log file
            db_connection_string: PostgreSQL connection string (if using postgres backend)
        """
        self.backend = storage_backend
        
        if storage_backend == "jsonl":
            self.log_file = Path(log_file_path)
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            if not self.log_file.exists():
                self.log_file.touch()
                logger.info(f"Created log file: {self.log_file}")
        elif storage_backend == "postgres":
            if not db_connection_string:
                raise ValueError("PostgreSQL backend requires db_connection_string")
            # PostgreSQL implementation would go here
            raise NotImplementedError("PostgreSQL backend not yet implemented")
    
    def log_question(
        self,
        query: str,
        model_response: str,
        detection_source: Literal[
            "auto_low_confidence",
            "user_negative_feedback", 
            "auto_no_results",
            "user_escalation"
        ],
        confidence_metrics: Optional[Dict[str, Any]] = None,
        retrieval_context: Optional[Dict[str, Any]] = None,
        user_feedback: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        message_index: Optional[int] = None,
        model_version: Optional[str] = None,
        message_id: Optional[str] = None
    ) -> str:
        """
        Create a new log entry for an unanswered question
        
        Args:
            query: The user's question
            model_response: The LLM's response (truncated to 5000 chars)
            detection_source: How this question was flagged
            confidence_metrics: Confidence scores and signals
            retrieval_context: Snapshot of retrieval results
            user_feedback: User feedback data (if applicable)
            session_id: Session identifier for anonymization
            message_index: Position in conversation
            model_version: LLM model identifier
            message_id: Frontend message ID (for linking)
        
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
            "model_response": model_response[:5000],  # Truncate to prevent huge logs
            "confidence_metrics": confidence_metrics or {},
            "retrieval_context_snapshot": retrieval_context or {},
            "detection_source": detection_source,
            "user_feedback": user_feedback,
            "metadata": {
                "session_id": anonymised_user_id,
                "message_index": message_index,
                "message_id": message_id,
                "model_version": model_version or "unknown"
            },
            "resolution_status": "pending",
            "admin_notes": None
        }
        
        if self.backend == "jsonl":
            self._append_to_jsonl(record)
        elif self.backend == "postgres":
            self._insert_to_postgres(record)
        
        logger.info(f"[UNANSWERED] {detection_source}: {query[:60]}...")
        return log_id
    
    def update_with_feedback(
        self,
        message_id: str,
        flag_reason: str,
        free_text_feedback: Optional[str] = None
    ) -> bool:
        """
        Update an existing log entry with user feedback
        
        Args:
            message_id: The message ID to find and update
            flag_reason: User-selected feedback category
            free_text_feedback: Optional free-form comment
        
        Returns:
            bool: True if record was found and updated
        """
        if self.backend != "jsonl":
            raise NotImplementedError("Feedback update only supported for JSONL backend")
        
        # Read all records
        records = []
        updated = False
        
        if not self.log_file.exists():
            return False
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    
                    # Check if this record matches the message_id
                    if record.get('metadata', {}).get('message_id') == message_id:
                        record['user_feedback'] = {
                            "flagged_at": datetime.now(timezone.utc).isoformat(),
                            "flag_reason": flag_reason,
                            "free_text_feedback": free_text_feedback
                        }
                        record['detection_source'] = "user_negative_feedback"
                        updated = True
                    
                    records.append(record)
        
        if updated:
            # Rewrite the entire file (atomic-ish via temp file + rename)
            temp_file = self.log_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                for record in records:
                    f.write(json.dumps(record) + '\n')
            
            temp_file.replace(self.log_file)
            logger.info(f"Updated record for message_id: {message_id}")
        
        return updated
    
    def _anonymise_session(self, session_id: str) -> str:
        """
        Create anonymised user ID from session ID using SHA256
        
        Args:
            session_id: Original session identifier
        
        Returns:
            str: Anonymised ID (format: "anon-<8-hex-chars>")
        """
        hash_obj = hashlib.sha256(session_id.encode())
        return f"anon-{hash_obj.hexdigest()[:8]}"
    
    def _append_to_jsonl(self, record: Dict) -> None:
        """
        Append record to JSONL file (atomic write operation)
        
        Args:
            record: Log entry dictionary
        """
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    def _insert_to_postgres(self, record: Dict) -> None:
        """PostgreSQL insertion (future implementation)"""
        raise NotImplementedError("PostgreSQL backend not yet implemented")
    
    def query_logs(
        self,
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
    ) -> Dict[str, Any]:
        """
        Query log entries with filters and pagination
        
        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip (pagination)
            min_confidence: Filter for confidence >= this value
            max_confidence: Filter for confidence < this value
            detection_source: Filter by detection source
            date_from: Filter for dates >= this (ISO 8601)
            date_to: Filter for dates <= this (ISO 8601)
            resolution_status: Filter by resolution status
            search: Full-text search in query field
            sort_by: Field to sort by ('timestamp' or 'confidence')
            sort_order: Sort direction ('asc' or 'desc')
        
        Returns:
            Dict containing total_count, questions list, and statistics
        """
        if self.backend == "jsonl":
            return self._query_jsonl(
                limit, offset, min_confidence, max_confidence,
                detection_source, date_from, date_to, resolution_status,
                search, sort_by, sort_order
            )
        elif self.backend == "postgres":
            return self._query_postgres(
                limit, offset, min_confidence, max_confidence,
                detection_source, date_from, date_to, resolution_status,
                search, sort_by, sort_order
            )
    
    def _query_jsonl(
        self,
        limit: int,
        offset: int,
        min_conf: Optional[float],
        max_conf: Optional[float],
        source: Optional[str],
        date_from: Optional[str],
        date_to: Optional[str],
        resolution: Optional[str],
        search: Optional[str],
        sort_by: str,
        sort_order: str
    ) -> Dict[str, Any]:
        """JSONL file-based query implementation"""
        questions = []
        
        if not self.log_file.exists():
            return {
                "total_count": 0,
                "returned_count": 0,
                "offset": offset,
                "questions": [],
                "statistics": self._empty_statistics()
            }
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                
                # Apply filters
                conf_score = record.get('confidence_metrics', {}).get('overall_score')
                
                if min_conf is not None and (conf_score is None or conf_score < min_conf):
                    continue
                if max_conf is not None and (conf_score is None or conf_score >= max_conf):
                    continue
                if source and record.get('detection_source') != source:
                    continue
                if date_from and record.get('timestamp', '') < date_from:
                    continue
                if date_to and record.get('timestamp', '') > date_to:
                    continue
                if resolution and record.get('resolution_status') != resolution:
                    continue
                if search and search.lower() not in record.get('query', '').lower():
                    continue
                
                questions.append(record)
        
        # Sort
        if sort_by == "confidence":
            questions.sort(
                key=lambda x: x.get('confidence_metrics', {}).get('overall_score', 0),
                reverse=(sort_order == "desc")
            )
        else:  # timestamp
            questions.sort(
                key=lambda x: x.get('timestamp', ''),
                reverse=(sort_order == "desc")
            )
        
        total_count = len(questions)
        paginated = questions[offset:offset + limit]
        
        # Calculate statistics from ALL matching questions (not just paginated)
        stats = self._calculate_statistics(questions)
        
        return {
            "total_count": total_count,
            "returned_count": len(paginated),
            "offset": offset,
            "questions": paginated,
            "statistics": stats
        }
    
    def _query_postgres(self, *args, **kwargs) -> Dict[str, Any]:
        """PostgreSQL query implementation (future)"""
        raise NotImplementedError("PostgreSQL backend not yet implemented")
    
    def _calculate_statistics(self, questions: List[Dict]) -> Dict:
        """
        Compute aggregate statistics from a list of questions
        
        Args:
            questions: List of log entry dictionaries
        
        Returns:
            Dict containing various statistics
        """
        if not questions:
            return self._empty_statistics()
        
        # Confidence scores
        confidences = [
            q['confidence_metrics'].get('overall_score', 0)
            for q in questions
            if 'confidence_metrics' in q and 'overall_score' in q['confidence_metrics']
        ]
        
        # Detection source breakdown
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
        
        # Resolution status breakdown
        resolution_breakdown = {}
        for q in questions:
            status = q.get('resolution_status', 'pending')
            resolution_breakdown[status] = resolution_breakdown.get(status, 0) + 1
        
        return {
            "avg_confidence": sum(confidences) / len(confidences) if confidences else None,
            "median_confidence": sorted(confidences)[len(confidences) // 2] if confidences else None,
            "detection_source_breakdown": source_breakdown,
            "top_categories": top_categories,
            "resolution_status_breakdown": resolution_breakdown,
            "total_with_user_feedback": sum(
                1 for q in questions if q.get('user_feedback') is not None
            )
        }
    
    def _empty_statistics(self) -> Dict:
        """Return empty statistics structure"""
        return {
            "avg_confidence": None,
            "median_confidence": None,
            "detection_source_breakdown": {},
            "top_categories": [],
            "resolution_status_breakdown": {},
            "total_with_user_feedback": 0
        }
    
    def get_statistics(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get high-level statistics for dashboard visualization
        
        Args:
            date_from: Optional date filter (ISO 8601)
            date_to: Optional date filter (ISO 8601)
        
        Returns:
            Dict containing statistics and trends
        """
        # Query all matching records
        result = self.query_logs(
            limit=999999,  # Get all records
            date_from=date_from,
            date_to=date_to
        )
        
        questions = result['questions']
        
        if not questions:
            return {
                "date_range": {"earliest_record": None, "latest_record": None, "total_days": 0},
                "totals": {"all_time_count": 0, "last_7_days": 0, "last_30_days": 0},
                "confidence_distribution": {"bins": [], "mean": None, "median": None},
                "temporal_trends": [],
                "top_failing_queries": []
            }
        
        # Date range
        timestamps = [q['timestamp'] for q in questions]
        earliest = min(timestamps)
        latest = max(timestamps)
        
        # Time-based counts
        now = datetime.now(timezone.utc)
        last_7_days = sum(
            1 for q in questions
            if (now - datetime.fromisoformat(q['timestamp'].replace('Z', '+00:00'))).days <= 7
        )
        last_30_days = sum(
            1 for q in questions
            if (now - datetime.fromisoformat(q['timestamp'].replace('Z', '+00:00'))).days <= 30
        )
        
        # Confidence distribution (10 bins: 0-0.1, 0.1-0.2, ..., 0.9-1.0)
        confidences = [
            q['confidence_metrics'].get('overall_score', 0)
            for q in questions
            if 'confidence_metrics' in q
        ]
        
        bins = []
        for i in range(10):
            min_val = i * 0.1
            max_val = (i + 1) * 0.1
            count = sum(1 for c in confidences if min_val <= c < max_val)
            bins.append({"min": round(min_val, 1), "max": round(max_val, 1), "count": count})
        
        return {
            "date_range": {
                "earliest_record": earliest,
                "latest_record": latest,
                "total_days": (
                    datetime.fromisoformat(latest.replace('Z', '+00:00')) -
                    datetime.fromisoformat(earliest.replace('Z', '+00:00'))
                ).days
            },
            "totals": {
                "all_time_count": len(questions),
                "last_7_days": last_7_days,
                "last_30_days": last_30_days
            },
            "confidence_distribution": {
                "bins": bins,
                "mean": sum(confidences) / len(confidences) if confidences else None,
                "median": sorted(confidences)[len(confidences) // 2] if confidences else None
            },
            "temporal_trends": self._calculate_temporal_trends(questions),
            "top_failing_queries": self._extract_top_failing_queries(questions)
        }
    
    def _calculate_temporal_trends(self, questions: List[Dict]) -> List[Dict]:
        """Calculate daily aggregations for time-series charts"""
        from collections import defaultdict
        
        daily_data = defaultdict(lambda: {"count": 0, "confidences": []})
        
        for q in questions:
            date = q['timestamp'][:10]  # YYYY-MM-DD
            daily_data[date]["count"] += 1
            
            conf = q.get('confidence_metrics', {}).get('overall_score')
            if conf is not None:
                daily_data[date]["confidences"].append(conf)
        
        trends = []
        for date in sorted(daily_data.keys()):
            data = daily_data[date]
            avg_conf = (
                sum(data["confidences"]) / len(data["confidences"])
                if data["confidences"] else None
            )
            trends.append({
                "date": date,
                "count": data["count"],
                "avg_confidence": avg_conf
            })
        
        return trends
    
    def _extract_top_failing_queries(self, questions: List[Dict], top_n: int = 10) -> List[Dict]:
        """
        Extract most common failing query patterns
        
        Note: This is a simplified implementation. Production version would use
        embedding clustering (HDBSCAN) to group semantically similar questions.
        """
        from collections import Counter
        
        # For now, just return top N unique queries by confidence
        query_data = [
            {
                "query": q['query'],
                "confidence": q.get('confidence_metrics', {}).get('overall_score', 0)
            }
            for q in questions
        ]
        
        # Sort by confidence (lowest first)
        query_data.sort(key=lambda x: x['confidence'])
        
        # Take top N unique queries
        seen = set()
        top_queries = []
        
        for item in query_data:
            if item['query'] not in seen:
                seen.add(item['query'])
                top_queries.append({
                    "query_pattern": item['query'][:100],  # Truncate for display
                    "count": 1,  # Would be clustered count in production
                    "avg_confidence": item['confidence'],
                    "example_query": item['query']
                })
                
                if len(top_queries) >= top_n:
                    break
        
        return top_queries
