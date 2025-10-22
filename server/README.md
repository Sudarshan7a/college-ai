# College AI - Backend Server

FastAPI backend server with RAG (Retrieval-Augmented Generation) system.

## 🚀 Quick Start

1. **Create virtual environment:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. **Install dependencies:**
```powershell
pip install -r requirements.txt
```

3. **Set up environment:**
```powershell
# Copy .env.example to .env and add your API key
copy .env.example .env
```

4. **Run the server:**
```powershell
python server.py
```

Server will be available at: http://localhost:8000

## 📚 Documentation

- **API Docs:** http://localhost:8000/docs (when server is running)
- **Setup Guide:** API_SERVER_GUIDE.md
- **Quick Start:** FASTAPI_QUICK_START.md
- **RAG System:** RAG_GUIDE.md
- **Re-ranker:** RERANKER_GUIDE.md

## 🗂️ Structure

```
server/
├── src/                    # Source code
│   ├── rag_system.py      # RAG implementation
│   ├── vector_store.py    # FAISS vector database
│   ├── embeddings.py      # MPNet embeddings
│   ├── reranker.py        # CrossEncoder re-ranker
│   ├── data_loader.py     # Document loading
│   ├── text_cleaner.py    # Text preprocessing
│   └── api_models.py      # Pydantic models
├── data/                   # Data storage
│   ├── extracted/         # Source documents
│   └── faiss_store/       # Vector database
├── server.py              # Main FastAPI server
└── requirements.txt       # Python dependencies
```
