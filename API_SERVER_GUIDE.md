# 🚀 College AI Backend API - Server Guide

## 📋 Table of Contents
1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [API Endpoints](#api-endpoints)
4. [Frontend Integration](#frontend-integration)
5. [Deployment](#deployment)
6. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The College AI Backend is a FastAPI server that provides a REST API for the College AI chatbot. It pre-loads all AI models (vector store, re-ranker, LLM) at startup for fast query responses.

### Features
✅ **Pre-loaded Models** - All models loaded once at startup  
✅ **Fast Responses** - ~1-2s for RAG queries, ~0.1-0.3s for search  
✅ **Auto Documentation** - Swagger UI at `/docs`  
✅ **CORS Enabled** - Ready for frontend integration  
✅ **Health Checks** - Monitor server status  
✅ **Statistics** - Track usage and performance  

### Architecture
```
Frontend → FastAPI Server → RAG System → Vector Store + LLM
                                       → Re-ranker
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```powershell
pip install fastapi uvicorn[standard] python-multipart aiofiles
```

### 2. Start the Server
```powershell
python server.py
```

Or with uvicorn:
```powershell
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

### 3. Expected Startup Output
```
============================================================
🚀 COLLEGE AI BACKEND - STARTING UP
============================================================

[1/3] Loading RAG system...
  ⏳ Loading vector store...
  ⏳ Loading re-ranker...
  ⏳ Initializing LLM...

✅ RAG system loaded successfully!
  📊 Vector Store: 143 vectors
  🎯 Re-ranker: Enabled
  🤖 LLM: llama-3.3-70b-versatile

============================================================
✅ SERVER READY FOR REQUESTS!
============================================================
📡 API Docs: http://localhost:8000/docs
🔍 Health Check: http://localhost:8000/api/health
============================================================
```

### 4. Test the Server
```powershell
python test_api.py
```

---

## 📡 API Endpoints

### Base URL
```
http://localhost:8000
```

### 1. Root Endpoint
**GET** `/`

Returns basic server information.

**Response:**
```json
{
  "message": "College AI Backend API",
  "status": "running",
  "docs": "/docs",
  "health": "/api/health"
}
```

---

### 2. Health Check
**GET** `/api/health`

Check if server is healthy and models are loaded.

**Response:**
```json
{
  "status": "healthy",
  "models_loaded": true,
  "uptime_seconds": 123.45,
  "vector_store_ready": true,
  "llm_ready": true,
  "total_vectors": 143
}
```

**Use case:** Frontend can poll this endpoint to check if backend is ready.

---

### 3. Search (Vector Search Only)
**POST** `/api/search`

Search for relevant documents without generating an answer. Faster than `/api/query`.

**Request:**
```json
{
  "query": "computer science courses",
  "top_k": 5
}
```

**Response:**
```json
{
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
```

**Processing time:** ~0.1-0.3 seconds

---

### 4. RAG Query (Full Answer)
**POST** `/api/query`

Ask a question and get an AI-generated answer with sources.

**Request:**
```json
{
  "query": "What are the placement statistics?",
  "top_k": 3,
  "include_sources": true
}
```

**Response:**
```json
{
  "answer": "The Computer Science Department has excellent placement statistics with 95% of students placed in top companies like Google, Microsoft, Amazon, and more...",
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
```

**Processing time:** ~1-2 seconds

---

### 5. Server Statistics
**GET** `/api/stats`

Get server statistics and usage metrics.

**Response:**
```json
{
  "total_queries": 42,
  "avg_response_time": 1.234,
  "uptime_seconds": 3600.5,
  "vector_store_info": {
    "total_vectors": 143,
    "dimension": 768,
    "model": "sentence-transformers/all-mpnet-base-v2",
    "reranker_enabled": true
  }
}
```

---

## 🌐 Frontend Integration

### JavaScript/React Example

```javascript
// Health Check
async function checkServerHealth() {
  try {
    const response = await fetch('http://localhost:8000/api/health');
    const data = await response.json();
    
    if (data.status === 'healthy') {
      console.log('✅ Server is ready!');
      return true;
    }
  } catch (error) {
    console.error('❌ Server not available:', error);
    return false;
  }
}

// Ask a Question
async function askQuestion(query) {
  try {
    const response = await fetch('http://localhost:8000/api/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: query,
        top_k: 3,
        include_sources: true
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    console.log('Answer:', data.answer);
    console.log('Sources:', data.sources);
    console.log('Processing time:', data.processing_time + 's');
    
    return data;
  } catch (error) {
    console.error('Error asking question:', error);
  }
}

// Usage
await checkServerHealth();
const result = await askQuestion('What are the placement statistics?');
```

### React Component Example

```jsx
import { useState, useEffect } from 'react';

function ChatBot() {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [serverReady, setServerReady] = useState(false);

  // Check server health on mount
  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/health');
      const data = await response.json();
      setServerReady(data.status === 'healthy');
    } catch (error) {
      setServerReady(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    
    try {
      const response = await fetch('http://localhost:8000/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: 3, include_sources: true })
      });

      const data = await response.json();
      setAnswer(data.answer);
    } catch (error) {
      setAnswer('Error: Could not get answer');
    } finally {
      setLoading(false);
    }
  };

  if (!serverReady) {
    return <div>⏳ Waiting for server to be ready...</div>;
  }

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question..."
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Processing...' : 'Ask'}
        </button>
      </form>
      
      {answer && (
        <div className="answer">
          <h3>Answer:</h3>
          <p>{answer}</p>
        </div>
      )}
    </div>
  );
}
```

### Python Requests Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Health check
response = requests.get(f"{BASE_URL}/api/health")
print(response.json())

# Ask a question
response = requests.post(
    f"{BASE_URL}/api/query",
    json={
        "query": "What are the placement statistics?",
        "top_k": 3,
        "include_sources": True
    }
)

data = response.json()
print(f"Answer: {data['answer']}")
print(f"Sources: {len(data['sources'])}")
```

---

## 🚀 Deployment

### Local Development
```powershell
# With auto-reload
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

### Production

1. **Disable auto-reload:**
   ```python
   # In server.py, change:
   uvicorn.run("server:app", reload=True)
   # To:
   uvicorn.run("server:app", reload=False)
   ```

2. **Use Gunicorn (Linux):**
   ```bash
   pip install gunicorn
   gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

3. **Update CORS origins:**
   ```python
   # In server.py, replace:
   allow_origins=["*"]
   # With:
   allow_origins=["https://yourfrontend.com"]
   ```

### Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t college-ai-backend .
docker run -p 8000:8000 -e GROQ_API_KEY=your_key college-ai-backend
```

---

## 🔧 Configuration

### Environment Variables

Create `.env` file:
```env
GROQ_API_KEY=your_groq_api_key_here
# Optional:
# OPENAI_API_KEY=your_openai_key
# GOOGLE_API_KEY=your_google_key
```

### Server Settings

Edit `server.py`:
```python
# Change port
uvicorn.run("server:app", port=8080)

# Change host
uvicorn.run("server:app", host="127.0.0.1")

# Disable reranker (faster but less accurate)
rag_system = CollegeRAG(use_reranker=False)
```

---

## 🐛 Troubleshooting

### Server won't start

**Error:** "Address already in use"
```powershell
# Find process using port 8000
netstat -ano | findstr :8000
# Kill the process (replace PID)
taskkill /PID <PID> /F
```

**Error:** "RAG system not loaded"
- Check if `.env` file exists with `GROQ_API_KEY`
- Check if `data/faiss_store/` exists (run `python src/vector_store.py` first)
- Check Python dependencies are installed

### Slow responses

**Issue:** Queries take >5 seconds
- Check internet connection (LLM calls require internet)
- Try disabling reranker: `CollegeRAG(use_reranker=False)`
- Check Groq API rate limits

### CORS errors in frontend

**Error:** "Access to fetch has been blocked by CORS policy"

In `server.py`, update CORS:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Health check shows unhealthy

**Issue:** `models_loaded: false`
- Server is still starting up (wait 30-60s)
- Check terminal for error messages during startup
- Verify `data/faiss_store/` exists

---

## 📊 Performance

### Typical Response Times
- **Health Check:** ~10ms
- **Search:** 100-300ms
- **RAG Query:** 1-2 seconds

### Resource Usage
- **RAM:** ~2-3 GB (models loaded)
- **CPU:** Minimal (1-5% idle, spikes during queries)
- **Startup Time:** 30-60 seconds

### Optimization Tips
1. Use `top_k=3` instead of `top_k=10` for faster queries
2. Disable reranker for 2x faster search (but less accurate)
3. Cache frequent queries (add Redis)
4. Use GPU for embeddings if available

---

## 🧪 Testing

### Run all tests:
```powershell
python test_api.py
```

### Test individual endpoints:
```powershell
# Health
curl http://localhost:8000/api/health

# Query (PowerShell)
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/query" `
  -ContentType "application/json" `
  -Body '{"query":"What are the placement statistics?","top_k":3}'

# Query (curl on Git Bash/Linux)
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What are the placement statistics?","top_k":3}'
```

---

## 📚 API Documentation

**Interactive docs:** http://localhost:8000/docs  
**ReDoc:** http://localhost:8000/redoc

These are automatically generated by FastAPI and include:
- All endpoints with descriptions
- Request/response schemas
- Try-it-out functionality
- Example payloads

---

## 🎯 Next Steps

1. ✅ Start the server
2. ✅ Test with `test_api.py`
3. ✅ Integrate with your frontend
4. 🚀 Deploy to production
5. 📊 Add monitoring and logging
6. 🔒 Add authentication (optional)

---

## 📞 Support

- **Documentation:** This guide + `/docs` endpoint
- **Issues:** Check troubleshooting section
- **Code:** See `server.py`, `src/api_models.py`, `src/rag_system.py`

**Happy Coding!** 🎉
