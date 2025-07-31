# Multi-Tenant RAG System

A production-grade **Multi-Tenant Retrieval-Augmented Generation (RAG) System** built with FastAPI, Qdrant, and Streamlit. This system provides secure, isolated RAG capabilities for multiple organizations with advanced document processing, vector search, and LLM integration.

## Features

### Backend Capabilities
- **Multi-Tenant Architecture**: Complete isolation between tenants with namespace-based data separation
- **Vector Database**: Qdrant integration with tenant-aware document storage and retrieval
- **LLM Integration**: Modular interface supporting OpenAI, Anthropic, and local models
- **Document Processing**: Support for PDF, TXT, and DOCX files with intelligent chunking
- **Authentication**: JWT-based authentication with role-based access control
- **Async Processing**: Background document processing and concurrent request handling
- **Horizontal Scaling**: Stateless services designed for Kubernetes deployment

### Frontend Interface
- **Streamlit UI**: Simple, detachable frontend for testing and demonstration
- **Tenant Selection**: Easy switching between different tenant contexts
- **Document Management**: Upload, process, and manage documents
- **RAG Chat Interface**: Interactive query interface with source attribution
- **Query History**: Track and analyze previous queries and responses

### Security Features
- **Tenant Isolation**: Strict data separation preventing cross-tenant access
- **JWT Authentication**: Secure token-based authentication with tenant context
- **Role-Based Access**: Admin, user, and viewer roles with appropriate permissions
- **Input Validation**: Comprehensive input validation and sanitization
- **Environment Variables**: Secure configuration management

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- OpenAI API key (optional, for LLM functionality)

### 1. Clone the Repository
```bash
git clone https://github.com/mominalix/Multi-Tenant-Retrieval-Augmented-Generation-RAG-System.git
cd Multi-Tenant-Retrieval-Augmented-Generation-RAG-System
```

### 2. Configure Environment Variables
```bash
# Copy example environment file
cp env.example .env

# Edit .env file with your configuration
# Add your OpenAI API key and other settings
```

### 3. Start the System
```bash
# Start all services with Docker Compose
docker-compose up -d

# Wait for services to initialize (about 30-60 seconds)
docker-compose logs -f backend
```

### 4. Access the Applications
- **Streamlit Frontend**: http://localhost:8501
- **FastAPI Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 5. Setup Sample Data (Optional)
```bash
# Run the setup script to create sample tenants and users
python scripts/setup_sample_data.py
```

##Usage Guide

### Creating Your First Tenant

1. **Access the API Documentation** at http://localhost:8000/docs
2. **Create an admin user** (you'll need to do this manually initially)
3. **Create a tenant** using the `/api/v1/auth/tenants` endpoint
4. **Create users** in the tenant using `/api/v1/auth/register`

### Using the Streamlit Interface

1. **Navigate** to http://localhost:8501
2. **Login** with your tenant credentials
3. **Upload documents** in the Documents section
4. **Wait for processing** (documents are processed in the background)
5. **Ask questions** in the Chat interface

### Sample Login Credentials (if using setup script)
- **Tenant**: Acme Corporation (subdomain: acme)
- **Email**: user@acme.com
- **Password**: user123

##Architecture

### System Components

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

### Multi-Tenant Data Flow

1. **Authentication**: User authenticates with tenant context
2. **Document Upload**: Files are uploaded and associated with tenant
3. **Processing**: Documents are chunked, embedded, and stored in Qdrant with tenant metadata
4. **RAG Query**: User queries are embedded and searched within tenant's document space
5. **Response Generation**: LLM generates response using retrieved context

### Tenant Isolation

- **Database Level**: All models include `tenant_id` for row-level security
- **Vector Store**: Qdrant uses metadata filtering for tenant isolation
- **API Level**: JWT tokens carry tenant context, validated on every request
- **File Storage**: Uploaded files are stored with tenant prefixes

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


##API Documentation

### Authentication Endpoints
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/tenants` - Create tenant (admin only)

### Document Management
- `POST /api/v1/documents/upload` - Upload document
- `GET /api/v1/documents/` - List documents
- `GET /api/v1/documents/{id}` - Get document details
- `DELETE /api/v1/documents/{id}` - Delete document

### RAG Queries
- `POST /api/v1/queries/rag` - Submit RAG query
- `POST /api/v1/queries/rag/stream` - Streaming RAG query
- `GET /api/v1/queries/history` - Get query history

##Troubleshooting

### Common Issues

**1. Database Connection Errors**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View database logs
docker-compose logs postgres
```

**2. Qdrant Connection Issues**
```bash
# Check Qdrant health
curl http://localhost:6333/health

# View Qdrant logs
docker-compose logs qdrant
```

**3. File Upload Failures**
- Check file size limits
- Verify upload directory permissions
- Ensure supported file types

**4. LLM API Errors**
- Verify API keys are set correctly
- Check API rate limits
- Ensure network connectivity

### Debug Mode
Enable debug mode for detailed error messages:
```bash
export DEBUG=true
```
