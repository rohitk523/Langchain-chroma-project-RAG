# RAG Chat Application

A full-stack RAG (Retrieval-Augmented Generation) chat application built with FastAPI, Next.js, OpenSearch, and Clerk authentication. Upload PDF documents and chat with them using AI.

## Features

- **Vector Database**: OpenSearch with k-NN search
- **Frontend**: Next.js with TypeScript and Tailwind CSS
- **Backend**: FastAPI with async support
- **Authentication**: Clerk (secure user management)
- **AI Integration**: OpenAI GPT models with LangChain
- **Document Processing**: PDF upload and text extraction
- **Chat Interface**: Real-time chat with document context
- **Deployment**: Docker containers with Railway/Heroku support

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│   Next.js App   │───▶│   FastAPI       │───▶│   OpenSearch    │
│   (Frontend)    │    │   (Backend)     │    │   (Vector DB)   │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                        │                        │
        │                        │                        │
        ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│   Clerk Auth    │    │   OpenAI API    │    │   Document      │
│   (Users)       │    │   (LLM)         │    │   Storage       │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Project Structure

```
langchain-chroma-project-RAG/
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/           # App router pages
│   │   ├── components/    # React components
│   │   └── hooks/         # Custom hooks
│   ├── public/            # Static assets
│   └── package.json
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── services/      # Business logic
│   │   ├── models/        # Pydantic models
│   │   ├── auth.py        # Authentication
│   │   └── main.py        # FastAPI app
│   ├── uploads/           # Temporary file storage
│   └── requirements.txt
├── docker-compose.yml     # Development environment
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Docker and Docker Compose (for development)
- OpenAI API key
- Clerk account

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/langchain-chroma-project-RAG.git
   cd langchain-chroma-project-RAG
   ```

2. **Set up environment variables**
   ```bash
   # Backend
   cp backend/env.dev.example backend/.env
   
   # Frontend
   cp frontend/env.local.example frontend/.env.local
   ```

3. **Fill in your API keys and credentials**
   - OpenAI API key
   - Clerk secret and publishable keys
   - OpenSearch credentials (use defaults for local development)

4. **Start the development environment**
   ```bash
   # Start OpenSearch with Docker Compose
   docker-compose up -d
   
   # Install and run backend
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Install and run frontend (in new terminal)
   cd frontend
   npm install
   npm run dev
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - OpenSearch: http://localhost:9200
   - OpenSearch Dashboards: http://localhost:5601

## Services Overview

### Development Services
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **OpenSearch**: http://localhost:9200

### Manual Development Setup

If you prefer to run services individually:

```bash
# Terminal 1: OpenSearch
docker-compose up opensearch-node1

# Terminal 2: Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Terminal 3: Frontend
cd frontend
npm install
npm run dev
```

## Deployment

### Railway Deployment

This project is configured for Railway deployment with three services:

1. **RAG-Chat-Frontend** (Next.js)
2. **RAG-Chat-Backend** (FastAPI)
3. **OpenSearch-Service** (OpenSearch)

### 1. Deploy OpenSearch Service

OpenSearch can be deployed using Railway's database add-ons or as a separate service.

### 2. Deploy Backend

```bash
# In backend directory
railway link [your-backend-project-id]
railway up
```

### 3. Deploy Frontend

```bash
# In frontend directory
railway link [your-frontend-project-id]
railway up
```

### 4. Environment Variables

Set these in your Railway dashboard:

```bash
# Backend Railway Environment
CLERK_SECRET_KEY=your_production_clerk_secret
OPENAI_API_KEY=your_production_openai_key
OPENSEARCH_HOST=your-opensearch-host.com
OPENSEARCH_PORT=443
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=your_secure_password

# Frontend Railway Environment
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_production_clerk_publishable_key
NEXT_PUBLIC_API_URL=https://your-backend-railway-url.railway.app
```

## Configuration

### Backend Configuration

Key settings in `backend/app/config.py`:

```python
# OpenSearch (adjust for deployment)
OPENSEARCH_HOST=localhost  # or your Railway service URL
OPENSEARCH_PORT=9200       # or 443 for Railway
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=admin
OPENSEARCH_USE_SSL=true
OPENSEARCH_VERIFY_CERTS=false
```

### Frontend Configuration

Key settings in `frontend/.env.local`:

```bash
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## API Endpoints

### Chat Endpoints
- `POST /api/chat` - Send chat message
- `GET /api/chat/{chat_id}/history` - Get chat history
- `GET /api/chats` - Get user's chats
- `DELETE /api/chat/{chat_id}` - Delete chat

### Document Endpoints
- `POST /api/upload` - Upload PDF document
- `GET /api/documents` - List user's documents

### Health Check
- `GET /` - API health check
- `GET /health` - Detailed health status

## Technology Stack

- **Frontend**: Next.js, TypeScript, Tailwind CSS, Clerk
- **Backend**: FastAPI, Python, Pydantic, LangChain
- **Vector Database**: OpenSearch with k-NN plugin
- **AI/ML**: OpenAI GPT, LangChain
- **Authentication**: Clerk
- **Deployment**: Railway, Docker
- **Development**: Docker Compose

## Troubleshooting

### Common Issues

1. **OpenSearch Connection**: Ensure OpenSearch service is running and accessible
2. **Authentication**: Check Clerk keys and configuration
3. **API Keys**: Verify OpenAI API key is valid and has credits
4. **CORS**: Check allowed origins in backend settings

### Debug Commands

```bash
# Check OpenSearch health
curl -X GET "localhost:9200/_cluster/health?pretty"

# Check backend logs
docker-compose logs backend

# Check OpenSearch logs
docker-compose logs opensearch-node1
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues and questions, please open an issue in the GitHub repository.