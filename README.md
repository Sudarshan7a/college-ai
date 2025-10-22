# College AI

AI-powered college information chatbot with RAG (Retrieval-Augmented Generation).

## 📁 Project Structure

```
college-ai/
├── app/                    # Next.js frontend (coming soon)
├── server/                 # Python FastAPI backend
│   ├── src/               # Backend source code
│   ├── data/              # Vector database & documents
│   ├── server.py          # FastAPI server
│   └── README.md          # Backend documentation
├── venv/                   # Python virtual environment
└── README.md              # This file
```

## 🚀 Quick Start

### Backend Server

```powershell
cd server
python -m venv ../venv
..\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python server.py
```

See [server/README.md](server/README.md) for detailed backend setup.

### Frontend (Coming Soon)

```powershell
cd app
npm install
npm run dev
```

## 📚 Documentation

- **Backend API:** [server/API_SERVER_GUIDE.md](server/API_SERVER_GUIDE.md)
- **RAG System:** [server/RAG_GUIDE.md](server/RAG_GUIDE.md)
- **Quick Start:** [server/FASTAPI_QUICK_START.md](server/FASTAPI_QUICK_START.md)

## 🔗 Links

- **API Docs:** http://localhost:8000/docs
- **Frontend:** http://localhost:3000 (coming soon)

## 📝 License

MIT
