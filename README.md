# RAG Chat Application

A full-stack RAG (Retrieval-Augmented Generation) chat application built with FastAPI, Next.js, ChromaDB, and Clerk authentication. Upload PDF documents and chat with them using AI.

## 🏗️ Architecture

- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS + shadcn/ui
- **Backend**: FastAPI + Python
- **Vector Database**: ChromaDB
- **Authentication**: Clerk
- **AI**: OpenAI GPT-3.5-turbo
- **Deployment**: Railway

## 🚀 Features

- 📄 **PDF Document Upload**: Upload and process PDF documents
- 💬 **AI Chat Interface**: Chat with your documents using RAG
- 📚 **Chat History**: Persistent chat sessions with history
- 🔐 **Authentication**: Secure user authentication with Clerk
- 🎨 **Modern UI**: Beautiful, responsive interface with shadcn/ui
- ☁️ **Cloud Deployment**: Ready for Railway deployment

## 📁 Project Structure

```
langchain-chroma-project-RAG/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py         # FastAPI application
│   │   ├── config.py       # Configuration settings
│   │   ├── auth.py         # Clerk authentication
│   │   ├── models/         # Pydantic models
│   │   └── services/       # Business logic
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile         # Production container
│   └── railway.json       # Railway config
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/           # App router pages
│   │   ├── components/    # React components
│   │   └── hooks/         # Custom hooks
│   ├── package.json       # Node dependencies
│   ├── Dockerfile         # Production container
│   └── railway.json       # Railway config
├── chroma-service/         # ChromaDB service
│   ├── Dockerfile         # ChromaDB container
│   └── railway.json       # Railway config
└── docker-compose.yml     # Local development
```

## 🛠️ Local Development Setup

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker and Docker Compose
- OpenAI API key
- Clerk account

### 1. Clone and Setup

```bash
git clone <repository-url>
cd langchain-chroma-project-RAG
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp env.dev.example .env

# Edit .env with your keys:
# - CLERK_SECRET_KEY
# - OPENAI_API_KEY
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment template
cp env.local.example .env.local

# Edit .env.local with your keys:
# - NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
# - CLERK_SECRET_KEY
```

### 4. Run with Docker Compose

```bash
# From project root
docker-compose up --build
```

This starts:
- ChromaDB: http://localhost:8001
- Backend API: http://localhost:8000
- Frontend: http://localhost:3000

### 5. Manual Development

If you prefer running services individually:

```bash
# Terminal 1: ChromaDB
cd chroma-service
docker build -t chroma-local .
docker run -p 8001:8000 chroma-local

# Terminal 2: Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 3: Frontend
cd frontend
npm run dev
```

## 🌐 Railway Deployment

### 1. Create Railway Projects

Create three separate Railway projects:
1. **RAG-Chat-Backend** (FastAPI)
2. **RAG-Chat-Frontend** (Next.js)
3. **RAG-Chat-ChromaDB** (ChromaDB)

### 2. Deploy ChromaDB Service

```bash
# Connect to Railway
railway login

# In chroma-service directory
cd chroma-service
railway link [your-chroma-project-id]
railway up
```

### 3. Deploy Backend

```bash
# In backend directory
cd backend
railway link [your-backend-project-id]

# Set environment variables in Railway dashboard:
# - CLERK_SECRET_KEY
# - OPENAI_API_KEY
# - CHROMA_HOST (your chroma service URL)
# - CHROMA_PORT=443

railway up
```

### 4. Deploy Frontend

```bash
# In frontend directory
cd frontend
railway link [your-frontend-project-id]

# Set environment variables in Railway dashboard:
# - NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
# - CLERK_SECRET_KEY
# - NEXT_PUBLIC_API_URL (your backend service URL)

railway up
```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```bash
# Required
CLERK_SECRET_KEY=sk_test_...
OPENAI_API_KEY=sk-...

# ChromaDB (adjust for deployment)
CHROMA_HOST=localhost  # or your Railway service URL
CHROMA_PORT=8001       # or 443 for Railway

# Optional
DEBUG=true
ALLOWED_ORIGINS=http://localhost:3000,https://your-frontend.railway.app
```

#### Frontend (.env.local)
```bash
# Required
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...

# API URL
NEXT_PUBLIC_API_URL=http://localhost:8000  # or your Railway backend URL
```

### Clerk Setup

1. Create a Clerk application at [clerk.com](https://clerk.com)
2. Enable email authentication
3. Copy your publishable and secret keys
4. Add your development/production URLs to allowed origins

## 📖 API Documentation

Once the backend is running, visit:
- Development: http://localhost:8000/docs
- Production: https://your-backend.railway.app/docs

### Key Endpoints

- `POST /api/chat` - Send chat message
- `GET /api/chat/{chat_id}/history` - Get chat history
- `GET /api/chats` - Get user's chats
- `POST /api/upload` - Upload PDF document
- `DELETE /api/chat/{chat_id}` - Delete chat

## 🧪 Usage

1. **Sign Up/Login**: Create account or login with Clerk
2. **Upload Document**: Click "Upload Document" and select a PDF
3. **Start Chatting**: Ask questions about your uploaded documents
4. **View Sources**: See source citations with similarity scores
5. **Manage Chats**: View chat history, create new chats, delete old ones

## 🔍 Troubleshooting

### Common Issues

1. **CORS Errors**: Check `ALLOWED_ORIGINS` in backend config
2. **Auth Errors**: Verify Clerk keys and webhook URLs
3. **ChromaDB Connection**: Ensure ChromaDB service is running and accessible
4. **File Upload Fails**: Check file size limits and PDF format

### Logs

```bash
# Backend logs
docker-compose logs backend

# Frontend logs  
docker-compose logs frontend

# ChromaDB logs
docker-compose logs chroma
```

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review Railway deployment logs
3. Open an issue on GitHub