# 🎯 Re-ranker Integration Guide

## What is Re-ranking?

Re-ranking improves search quality by using a more accurate (but slower) model to re-order the top results from FAISS.

**2-Stage Search:**
1. **FAISS (Fast):** Retrieves top 10 candidates using vector similarity
2. **CrossEncoder (Accurate):** Re-ranks those 10 to find the best 5

**Result:** Better relevance without sacrificing too much speed!

---

## 🚀 Quick Start

### 1. Basic Usage (Automatic Re-ranking)

```python
from src.vector_store import FaissVectorStore

# Load vector store
store = FaissVectorStore()
store.load()

# Enable re-ranker
store.enable_reranker()  # Uses cross-encoder/ms-marco-MiniLM-L-6-v2 by default

# Query (automatically re-ranked)
results = store.query("What are the placement statistics?", top_k=5)

for i, r in enumerate(results, 1):
    print(f"{i}. Rerank Score: {r['rerank_score']:.4f}")
    print(f"   FAISS Distance: {r['distance']:.3f}")
    print(f"   Category: {r['metadata']['category']}")
    print(f"   Text: {r['metadata']['text'][:100]}...\n")
```

### 2. Compare With and Without Re-ranking

```python
from src.vector_store import FaissVectorStore

store = FaissVectorStore()
store.load()

query = "Tell me about computer science courses"

# Without reranking
print("🔵 FAISS Only:")
results_faiss = store.query(query, top_k=5, rerank=False)
for i, r in enumerate(results_faiss, 1):
    print(f"{i}. {r['distance']:.3f} - {r['metadata']['category']}")

# With reranking
print("\n🟢 FAISS + Re-ranker:")
store.enable_reranker()
results_reranked = store.query(query, top_k=5, rerank=True)
for i, r in enumerate(results_reranked, 1):
    print(f"{i}. Rerank: {r['rerank_score']:.4f} - {r['metadata']['category']}")
```

### 3. Use Different Re-ranker Models

```python
# Default model (recommended)
store.enable_reranker("cross-encoder/ms-marco-MiniLM-L-6-v2")

# Larger, more accurate model
store.enable_reranker("cross-encoder/ms-marco-MiniLM-L-12-v2")

# Fastest model
store.enable_reranker("cross-encoder/ms-marco-TinyBERT-L-2-v2")
```

---

## 📊 Performance Comparison

| Method | Speed | Accuracy | Use Case |
|--------|-------|----------|----------|
| **FAISS Only** | ⚡⚡⚡ Very Fast | ⭐⭐ Good | Real-time search, high-volume queries |
| **FAISS + Re-ranker** | ⚡⚡ Fast | ⭐⭐⭐⭐ Excellent | User-facing search, Q&A systems |
| **CrossEncoder Only** | ⚡ Slow | ⭐⭐⭐⭐⭐ Best | Offline analysis |

**Recommendation:** Use FAISS + Re-ranker for production!

---

## 🎯 How It Works

### FAISS Search (Approximate)
```
Query: "What are placement statistics?"

FAISS Returns (by distance):
1. Distance: 0.85 - "The CSE department has 200 students..."
2. Distance: 0.91 - "95% placements with 6.5 LPA average..."  ← Actually most relevant!
3. Distance: 0.94 - "Library has 50,000 books..."
```

### After Re-ranking (Accurate)
```
CrossEncoder Re-ranks:
1. Rerank: 8.23 - "95% placements with 6.5 LPA average..."  ← Now on top!
2. Rerank: 6.45 - "The CSE department has 200 students..."
3. Rerank: 2.12 - "Library has 50,000 books..."
```

**Re-ranker fixes the ordering!**

---

## 🔧 Configuration

### In `src/vector_store.py`

```python
# Retrieve more candidates for re-ranking
initial_k = top_k * 2  # Get 10 results, rerank to top 5

# You can adjust this multiplier based on your needs
```

### Model Sizes

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| TinyBERT-L-2 | 17MB | Fastest | Good |
| MiniLM-L-6 (default) | 80MB | Fast | Excellent |
| MiniLM-L-12 | 125MB | Medium | Best |

---

## 🧪 Testing

### Standalone Re-ranker Test
```powershell
python src\reranker.py
```

**Expected Output:**
```
RE-RANKER DEMO
============================================================

Query: 'What are the placement statistics?'

📊 Original Results (sorted by FAISS distance):
1. Distance: 1.20 | facilities
   The library has 50,000 books...
2. Distance: 1.10 | departments
   Computer Science department offers AI...
3. Distance: 0.90 | placements
   95% placements in 2024 with average package of 6.5 LPA...

✨ Re-ranked Results (sorted by semantic relevance):
1. Rerank Score: 8.2341 | Distance: 0.90
   Category: placements
   95% placements in 2024 with average package of 6.5 LPA...

📈 Statistics:
   Order changes: 2/3 (67%)

✅ Re-ranking improves relevance!
```

### Full Vector Store Test
```powershell
python src\vector_store.py
```

Look for **EXAMPLE 3** in the output showing re-ranker comparison.

---

## 🚨 Troubleshooting

### Issue: "Reranker not available"
```powershell
# Ensure sentence-transformers is installed with CrossEncoder support
pip install sentence-transformers>=2.2.0
```

### Issue: Re-ranking is slow
**Solution:** Use smaller model or disable for high-volume queries
```python
store.enable_reranker("cross-encoder/ms-marco-TinyBERT-L-2-v2")

# Or disable dynamically
store.disable_reranker()
```

### Issue: Re-ranking doesn't improve results
**Possible causes:**
1. FAISS embeddings already very good (MPNet is accurate)
2. Query too vague
3. Not enough candidates to re-rank

**Solution:** Increase `initial_k`:
```python
# In vector_store.py, query() method
initial_k = top_k * 3  # Get 15 results, rerank to top 5
```

---

## 💡 Best Practices

### 1. **Enable Re-ranker for User Queries**
```python
# Good for user-facing search
store.enable_reranker()
results = store.query(user_question, top_k=5)
```

### 2. **Disable for Batch Processing**
```python
# Good for processing 1000s of queries
store.disable_reranker()
for query in large_query_list:
    results = store.query(query, top_k=5, rerank=False)
```

### 3. **Use Per-Query Control**
```python
# Enable globally but override for specific queries
store.enable_reranker()

# Important query - use reranking
results = store.query("critical question", top_k=5, rerank=True)

# Simple query - skip reranking
results = store.query("simple lookup", top_k=5, rerank=False)
```

### 4. **Cache Re-ranker Model**
```python
# Load once at startup (already done in vector_store.py)
store = FaissVectorStore()
store.load()
store.enable_reranker()  # Model loaded once

# Reuse for multiple queries
for query in user_queries:
    results = store.query(query, top_k=5)  # Fast!
```

---

## 📈 Expected Improvements

### Typical Results

**Before Re-ranking:**
- Query: "What are placement statistics?"
- Top result: Distance 0.92 - "CSE department overview" (wrong!)

**After Re-ranking:**
- Query: "What are placement statistics?"
- Top result: Rerank 8.5 - "95% placements with 6.5 LPA" (correct!)

**Accuracy Improvement:** +15-25% on average

---

## 🎓 When to Use Re-ranking

### ✅ Use Re-ranking When:
- User-facing Q&A systems
- Chatbot responses need high accuracy
- Query relevance is critical
- Processing < 100 queries/second

### ❌ Skip Re-ranking When:
- Real-time search (< 50ms required)
- Batch processing 1000s of queries
- FAISS embeddings already very accurate
- Resource-constrained environment

---

## 📚 Additional Resources

- **Code:** `src/reranker.py` - Standalone re-ranker implementation
- **Integration:** `src/vector_store.py` - Vector store with re-ranker
- **Models:** [Sentence-Transformers CrossEncoders](https://www.sbert.net/docs/pretrained_cross-encoders.html)

---

**Re-ranking = Better Results! 🎯**
