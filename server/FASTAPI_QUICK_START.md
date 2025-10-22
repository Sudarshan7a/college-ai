# FastAPI Server - Quick Start Notes

## ✅ What's Been Completed

All FastAPI backend implementation is complete and committed to the `feature/fastapi-backend` branch:

- ✅ **server.py** - Main FastAPI server with pre-loaded RAG system
- ✅ **src/api_models.py** - Pydantic models for requests/responses
- ✅ **test_api.py** - Comprehensive API testing script
- ✅ **API_SERVER_GUIDE.md** - Complete documentation with frontend examples
- ✅ **Pushed to GitHub** - Branch available for PR

## 🚀 How to Start the Server

### Method 1: Direct Python

```powershell
python server.py
```

### Method 2: Uvicorn

```powershell
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

## ⏳ First Startup - TensorFlow Loading

**Important:** The first time you start the server, TensorFlow will take 30-60 seconds to load. This is normal on Windows.

You'll see:

1. "College AI Project v0.1.0 initialized successfully!"
2. Then a pause (TensorFlow loading - this is normal!)
3. Then the startup sequence will continue

### What You Should See:

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

## 🧪 Testing

Once the server is running:

### Terminal 1 (Server):

```powershell
python server.py
# Wait for "SERVER READY FOR REQUESTS!"
```

### Terminal 2 (Tests):

```powershell
python test_api.py
```

### Or Test Manually:

**Browser:**

- Interactive docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

**PowerShell:**

```powershell
# Health check
Invoke-RestMethod http://localhost:8000/api/health

# Query
$body = @{
    query = "What are the placement statistics?"
    top_k = 3
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/query" `
  -ContentType "application/json" -Body $body
```

## 📊 API Endpoints

| Endpoint      | Method | Purpose             | Response Time |
| ------------- | ------ | ------------------- | ------------- |
| `/`           | GET    | Server info         | ~10ms         |
| `/api/health` | GET    | Health check        | ~10ms         |
| `/api/search` | POST   | Vector search only  | ~100-300ms    |
| `/api/query`  | POST   | Full RAG (with LLM) | ~1-2s         |
| `/api/stats`  | GET    | Server statistics   | ~10ms         |

## 🔗 Next Steps

1. ✅ **Test the server** - Run `python server.py` and verify startup
2. ✅ **Run tests** - Execute `python test_api.py`
3. 🚀 **Integrate frontend** - Use examples in `API_SERVER_GUIDE.md`
4. 📝 **Create PR** - Merge `feature/fastapi-backend` into `main`

## 📚 Documentation

- **Full Guide:** `API_SERVER_GUIDE.md`
- **API Models:** See `src/api_models.py`
- **Server Code:** See `server.py`
- **Interactive Docs:** http://localhost:8000/docs (when server is running)

## 🐛 Troubleshooting

### Server won't start

- Check if port 8000 is already in use
- Verify `.env` file exists with `GROQ_API_KEY`
- Ensure `data/faiss_store/` exists (run `python src/vector_store.py` first)

### "Models not loaded" error

- Server is still starting up - wait 30-60 seconds
- Check terminal for error messages

### Import errors

```powershell
pip install fastapi uvicorn[standard] python-multipart aiofiles
```

---

**Happy Coding!** 🎉

For complete documentation, see `API_SERVER_GUIDE.md`
