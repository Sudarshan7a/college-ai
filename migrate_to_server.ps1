# Migration Script: Move Python Backend to server/ folder
# Keeps app/ folder at root for Next.js

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MIGRATING PYTHON BACKEND TO server/" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Items to move to server/
$itemsToMove = @(
    "src",
    "data",
    "notebooks",
    "doc",
    "server.py",
    "test_api.py",
    "test_rag.py",
    "quick_test_rag.py",
    "requirements.txt",
    ".env",
    ".env.example",
    ".env.local",
    "API_SERVER_GUIDE.md",
    "FASTAPI_QUICK_START.md",
    "RAG_GUIDE.md",
    "RERANKER_GUIDE.md",
    "UPGRADE_SUMMARY.md",
    "VECTOR_SEARCH_UPGRADE.md",
    "TEST_GUIDE.md"
)

# Create server directory structure if needed
if (-not (Test-Path "server")) {
    New-Item -ItemType Directory -Path "server" -Force | Out-Null
    Write-Host "[CREATE] Created server/ directory" -ForegroundColor Green
}

# Move items
foreach ($item in $itemsToMove) {
    if (Test-Path $item) {
        Write-Host "[MOVE] Moving $item to server/" -ForegroundColor Yellow
        Move-Item -Path $item -Destination "server/" -Force
    } else {
        Write-Host "[SKIP] $item does not exist" -ForegroundColor Gray
    }
}

# Create server/README.md
$serverReadme = @"
# College AI - Backend Server

FastAPI backend server with RAG (Retrieval-Augmented Generation) system.

## 🚀 Quick Start

1. **Create virtual environment:**
``````powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
``````

2. **Install dependencies:**
``````powershell
pip install -r requirements.txt
``````

3. **Set up environment:**
``````powershell
# Copy .env.example to .env and add your API key
copy .env.example .env
``````

4. **Run the server:**
``````powershell
python server.py
``````

Server will be available at: http://localhost:8000

## 📚 Documentation

- **API Docs:** http://localhost:8000/docs (when server is running)
- **Setup Guide:** API_SERVER_GUIDE.md
- **Quick Start:** FASTAPI_QUICK_START.md
- **RAG System:** RAG_GUIDE.md
- **Re-ranker:** RERANKER_GUIDE.md

## 🗂️ Structure

``````
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
``````
"@

Set-Content -Path "server/README.md" -Value $serverReadme
Write-Host "[CREATE] Created server/README.md" -ForegroundColor Green

# Update root README.md
$rootReadme = @"
# College AI

AI-powered college information chatbot with RAG (Retrieval-Augmented Generation).

## 📁 Project Structure

``````
college-ai/
├── app/                    # Next.js frontend (coming soon)
├── server/                 # Python FastAPI backend
│   ├── src/               # Backend source code
│   ├── data/              # Vector database & documents
│   ├── server.py          # FastAPI server
│   └── README.md          # Backend documentation
├── venv/                   # Python virtual environment
└── README.md              # This file
``````

## 🚀 Quick Start

### Backend Server

``````powershell
cd server
python -m venv ../venv
..\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python server.py
``````

See [server/README.md](server/README.md) for detailed backend setup.

### Frontend (Coming Soon)

``````powershell
cd app
npm install
npm run dev
``````

## 📚 Documentation

- **Backend API:** [server/API_SERVER_GUIDE.md](server/API_SERVER_GUIDE.md)
- **RAG System:** [server/RAG_GUIDE.md](server/RAG_GUIDE.md)
- **Quick Start:** [server/FASTAPI_QUICK_START.md](server/FASTAPI_QUICK_START.md)

## 🔗 Links

- **API Docs:** http://localhost:8000/docs
- **Frontend:** http://localhost:3000 (coming soon)

## 📝 License

MIT
"@

Set-Content -Path "README.md" -Value $rootReadme
Write-Host "[UPDATE] Updated root README.md" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "MIGRATION COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. cd server" -ForegroundColor White
Write-Host "2. python server.py" -ForegroundColor White
Write-Host ""
Write-Host "Note: You may need to update .gitignore" -ForegroundColor Yellow
