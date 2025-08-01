# Multi-Tenant RAG System

![Demo](./demo.gif)
*Demo of the Multi-Tenant RAG System in action*

A production-grade Multi-Tenant Retrieval-Augmented Generation (RAG) System built with FastAPI, Qdrant, and Streamlit. This system provides secure, isolated RAG capabilities for multiple organizations with advanced document processing, vector search, and LLM integration.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │────│   FastAPI       │────│   PostgreSQL    │
│   Frontend      │    │   Backend       │    │   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                               ├─────────────────────────────────┐
                               │                                 │
                    ┌─────────────────┐              ┌─────────────────┐
                    │     Qdrant      │              │      Redis      │
                    │ Vector Database │              │     Cache       │
                    └─────────────────┘              └─────────────────┘
```

## Features

**Core Capabilities**
- Multi-tenant architecture with complete data isolation
- Vector database integration using Qdrant
- Support for multiple LLM providers (OpenAI, Anthropic, local models)
- Document processing for PDF, TXT, and DOCX files
- JWT-based authentication with role-based access control
- Background document processing
- Horizontal scaling for production deployments

**User Interface**
- Clean web interface built with Streamlit
- Document upload and management
- Interactive chat interface with source attribution
- Query history and analytics

**Security**
- Strict tenant isolation at database and vector store level
- Secure authentication with tenant context
- Input validation and sanitization
- Environment-based configuration management

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- OpenAI API key (optional, for LLM functionality)

**1. Clone and Setup**
```bash
git clone https://github.com/mominalix/Multi-Tenant-Retrieval-Augmented-Generation-RAG-System.git
cd Multi-Tenant-Retrieval-Augmented-Generation-RAG-System
cp env.example .env
# Edit .env with your API keys and configuration
```

**2. Start the System**
```bash
docker-compose up -d
```

**3. Access the Application**
- Frontend: http://localhost:8501
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

**4. Optional Sample Data**
```bash
python scripts/setup_sample_data.py
```

## Usage Guide

**Getting Started**
1. Navigate to http://localhost:8501
2. Create a new organization or login with existing credentials
3. Upload documents in the Documents section
4. Wait for processing (runs in background)
5. Ask questions in the Chat interface

**Sample Credentials (with setup script)**
- Email: user@acme.com
- Password: user123

**How It Works**
1. User authenticates with tenant context
2. Documents are uploaded and processed with tenant isolation
3. Files are chunked, embedded, and stored in vector database
4. Queries search only within tenant's document space
5. LLM generates responses using retrieved context

**Security Model**
- Database-level tenant isolation with row-level security
- Vector store uses metadata filtering for tenant separation
- JWT tokens carry tenant context for all requests
- File storage uses tenant-specific prefixes

## Development

### Local Development Setup

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Setup Local Databases**
```bash
# Start only the databases
docker-compose up -d postgres redis qdrant
```

3. **Run Backend Locally**
```bash
# Set environment variables
export DATABASE_URL="postgresql://postgres:password@localhost:5432/multi_tenant_rag"
export QDRANT_HOST="localhost"
export REDIS_URL="redis://localhost:6379"

# Run the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. **Run Frontend Locally**
```bash
streamlit run frontend/streamlit_app.py --server.port 8501
```

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Code Quality
```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Lint code
flake8 app/ tests/
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `QDRANT_HOST` | Qdrant server host | localhost |
| `QDRANT_PORT` | Qdrant server port | 6333 |
| `OPENAI_API_KEY` | OpenAI API key | Optional |
| `ANTHROPIC_API_KEY` | Anthropic API key | Optional |
| `JWT_SECRET_KEY` | JWT signing secret | Required |
| `MAX_FILE_SIZE_MB` | Maximum upload file size | 10 |
| `EMBEDDING_MODEL` | Sentence transformer model | all-MiniLM-L6-v2 |

### Docker Compose Customization

Edit `docker-compose.yml` to customize:
- Resource limits
- Volume mounts
- Network configuration
- Environment variables

## Deployment

### Production Deployment

1. **Kubernetes Deployment**
```bash
# Create namespace
kubectl create namespace multi-tenant-rag

# Deploy using provided Kubernetes manifests
kubectl apply -f k8s/ -n multi-tenant-rag
```

2. **Docker Swarm Deployment**
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.prod.yml rag-stack
```

### Scaling Considerations

- **Backend**: Scale FastAPI instances horizontally
- **Database**: Use PostgreSQL with read replicas
- **Vector Store**: Qdrant supports clustering
- **File Storage**: Use S3 or similar for production file storage

### Security Checklist

- [ ] Change default JWT secret key
- [ ] Use strong passwords for database
- [ ] Enable HTTPS/TLS in production
- [ ] Configure proper firewall rules
- [ ] Set up monitoring and logging
- [ ] Regular security updates

## Monitoring

### Health Checks
- **API Health**: `GET /health`
- **Detailed Health**: `GET /health/detailed`
- **Database**: Connection and query tests
- **Vector Store**: Qdrant connectivity
- **LLM Services**: Provider availability

### Logging
The system uses structured logging with JSON format:
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "logger": "app.services.rag",
  "message": "RAG query completed",
  "tenant_id": "uuid",
  "user_id": "uuid",
  "processing_time_ms": 150
}
```


## API Documentation

**Authentication**
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration  
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/tenants` - Create tenant (admin only)

**Document Management**
- `POST /api/v1/documents/upload` - Upload document
- `GET /api/v1/documents/` - List documents
- `GET /api/v1/documents/{id}` - Get document details
- `DELETE /api/v1/documents/{id}` - Delete document

**RAG Queries**
- `POST /api/v1/queries/rag` - Submit RAG query
- `POST /api/v1/queries/rag/stream` - Streaming RAG query
- `GET /api/v1/queries/history` - Get query history

## Troubleshooting

**Common Issues**

Database Connection Errors
```bash
docker-compose ps postgres
docker-compose logs postgres
```

Qdrant Connection Issues
```bash
curl http://localhost:6333/health
docker-compose logs qdrant
```

File Upload Failures
- Check file size limits (default 10MB)
- Verify supported file types (PDF, TXT, DOCX)
- Check upload directory permissions

LLM API Errors
- Verify API keys in .env file
- Check API rate limits
- Ensure network connectivity

**Debug Mode**
```bash
export DEBUG=true
docker-compose restart backend
```
