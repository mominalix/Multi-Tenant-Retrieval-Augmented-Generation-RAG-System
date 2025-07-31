# Deployment Guide

This guide covers production deployment options for the Multi-Tenant RAG System.

## Overview

The system consists of several components that need to be deployed and configured:

- **FastAPI Backend** - Main application server
- **Streamlit Frontend** - User interface (optional)
- **PostgreSQL** - Primary database
- **Qdrant** - Vector database
- **Redis** - Caching and session storage

## Prerequisites

### Hardware Requirements

**Minimum (Development/Testing):**
- 4 CPU cores
- 8 GB RAM
- 50 GB SSD storage
- 10 Mbps network

**Recommended (Production):**
- 8 CPU cores
- 16 GB RAM
- 200 GB SSD storage
- 100 Mbps network

**Scale (High Volume):**
- 16+ CPU cores
- 32+ GB RAM
- 500+ GB SSD storage
- 1 Gbps network

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- Kubernetes 1.20+ (for K8s deployment)
- SSL/TLS certificates
- Domain name and DNS access

## Environment Configuration

### Environment Variables

Create a production `.env` file:

```bash
# Database Configuration
DATABASE_URL=postgresql://rag_user:secure_password@postgres-host:5432/multi_tenant_rag
REDIS_URL=redis://redis-host:6379/0

# Qdrant Configuration
QDRANT_HOST=qdrant-host
QDRANT_PORT=6333
QDRANT_API_KEY=your-qdrant-api-key

# Security
JWT_SECRET_KEY=your-very-secure-jwt-secret-key-change-this
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# LLM Configuration
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
DEFAULT_LLM_PROVIDER=openai

# Application
APP_NAME=Multi-Tenant RAG System
APP_VERSION=1.0.0
DEBUG=false
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com

# Storage
MAX_FILE_SIZE_MB=10
UPLOAD_DIR=/app/uploads
ALLOWED_FILE_TYPES=pdf,txt,docx

# Monitoring
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Security Configuration

1. **Generate Secure JWT Secret:**
```bash
openssl rand -hex 32
```

2. **Database Security:**
```bash
# Create dedicated database user
CREATE USER rag_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE multi_tenant_rag TO rag_user;
```

3. **SSL/TLS Certificates:**
```bash
# Using Let's Encrypt
certbot certonly --webroot -w /var/www/html -d yourdomain.com
```

## Deployment Options

### Option 1: Docker Compose (Recommended for Small/Medium Scale)

#### 1. Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    restart: unless-stopped
    environment:
      POSTGRES_DB: multi_tenant_rag
      POSTGRES_USER: rag_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - rag-network
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - rag-network
    deploy:
      resources:
        limits:
          memory: 512M

  qdrant:
    image: qdrant/qdrant:v1.7.0
    restart: unless-stopped
    environment:
      QDRANT__SERVICE__HTTP_PORT: 6333
      QDRANT__SERVICE__API_KEY: ${QDRANT_API_KEY}
    volumes:
      - qdrant_data:/qdrant/storage
    networks:
      - rag-network
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql://rag_user:${POSTGRES_PASSWORD}@postgres:5432/multi_tenant_rag
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      QDRANT_HOST: qdrant
      QDRANT_API_KEY: ${QDRANT_API_KEY}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      DEBUG: false
    volumes:
      - upload_data:/app/uploads
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis
      - qdrant
    networks:
      - rag-network
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
      replicas: 2

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - backend
    networks:
      - rag-network

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
  upload_data:

networks:
  rag-network:
    driver: bridge
```

#### 2. Nginx Configuration

Create `nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    server {
        listen 80;
        server_name yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        ssl_certificate /etc/ssl/certs/fullchain.pem;
        ssl_certificate_key /etc/ssl/certs/privkey.pem;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

        # API routes
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Increase timeouts for large file uploads
            proxy_connect_timeout 300s;
            proxy_send_timeout 300s;
            proxy_read_timeout 300s;
            client_max_body_size 50M;
        }

        # Health check
        location /health {
            proxy_pass http://backend;
            access_log off;
        }

        # Static files (if any)
        location /static/ {
            alias /var/www/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

#### 3. Deploy

```bash
# Set environment variables
export POSTGRES_PASSWORD=your-secure-db-password
export REDIS_PASSWORD=your-secure-redis-password
export QDRANT_API_KEY=your-qdrant-api-key
export JWT_SECRET_KEY=your-jwt-secret
export OPENAI_API_KEY=your-openai-key

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Monitor
docker-compose -f docker-compose.prod.yml logs -f
```

### Option 2: Kubernetes Deployment

#### 1. Namespace and Secrets

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: multi-tenant-rag
---
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: rag-secrets
  namespace: multi-tenant-rag
type: Opaque
stringData:
  postgres-password: your-secure-db-password
  redis-password: your-secure-redis-password
  jwt-secret: your-jwt-secret
  openai-api-key: your-openai-key
  qdrant-api-key: your-qdrant-api-key
```

#### 2. Database Deployment

```yaml
# postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: multi-tenant-rag
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: multi_tenant_rag
        - name: POSTGRES_USER
          value: rag_user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: rag-secrets
              key: postgres-password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: multi-tenant-rag
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
```

#### 3. Backend Deployment

```yaml
# backend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: multi-tenant-rag
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: your-registry/multi-tenant-rag-backend:latest
        env:
        - name: DATABASE_URL
          value: postgresql://rag_user:$(POSTGRES_PASSWORD)@postgres:5432/multi_tenant_rag
        - name: REDIS_URL
          value: redis://:$(REDIS_PASSWORD)@redis:6379/0
        - name: QDRANT_HOST
          value: qdrant
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: rag-secrets
              key: jwt-secret
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: rag-secrets
              key: openai-api-key
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: rag-secrets
              key: postgres-password
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: rag-secrets
              key: redis-password
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: multi-tenant-rag
spec:
  selector:
    app: backend
  ports:
  - port: 8000
    targetPort: 8000
```

#### 4. Ingress Configuration

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: rag-ingress
  namespace: multi-tenant-rag
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: rag-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 8000
```

#### 5. Deploy to Kubernetes

```bash
# Apply manifests
kubectl apply -f namespace.yaml
kubectl apply -f secrets.yaml
kubectl apply -f postgres.yaml
kubectl apply -f redis.yaml
kubectl apply -f qdrant.yaml
kubectl apply -f backend.yaml
kubectl apply -f ingress.yaml

# Check status
kubectl get pods -n multi-tenant-rag
kubectl logs -f deployment/backend -n multi-tenant-rag
```

## Database Migrations

### Alembic Setup

```bash
# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

### Backup Strategy

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h postgres-host -U rag_user multi_tenant_rag > /backups/rag_backup_$DATE.sql
gzip /backups/rag_backup_$DATE.sql

# Keep only last 7 days
find /backups -name "rag_backup_*.sql.gz" -mtime +7 -delete
```

## Monitoring and Logging

### Health Checks

Configure monitoring for:
- API endpoints (`/health`, `/health/detailed`)
- Database connectivity
- Vector store health
- File system usage
- Memory and CPU usage

### Logging

**Structured logging configuration:**

```python
# logging_config.py
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
        }
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "formatter": "json",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "level": "INFO",
            "formatter": "json",
            "class": "logging.FileHandler",
            "filename": "/app/logs/app.log"
        }
    },
    "loggers": {
        "": {
            "handlers": ["default", "file"],
            "level": "INFO",
            "propagate": False
        }
    }
}
```

### Metrics Collection

**Prometheus metrics:**

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')
ACTIVE_USERS = Gauge('active_users_total', 'Active users')
DOCUMENT_COUNT = Gauge('documents_total', 'Total documents', ['tenant_id'])
```

## Security Hardening

### Application Security

1. **Environment Variables:**
   - Use secrets management (K8s secrets, Docker secrets)
   - Never commit secrets to version control
   - Rotate secrets regularly

2. **Network Security:**
   - Use TLS everywhere
   - Implement proper CORS policies
   - Set up WAF (Web Application Firewall)

3. **Database Security:**
   - Use connection pooling with SSL
   - Regular security updates
   - Principle of least privilege

### Container Security

```dockerfile
# Security-hardened Dockerfile
FROM python:3.11-slim

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Set security options
USER app
WORKDIR /app

# Remove unnecessary files
RUN rm -rf /tmp/* /var/tmp/*

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

## Performance Optimization

### Database Optimization

```sql
-- Create indexes for better performance
CREATE INDEX CONCURRENTLY idx_documents_tenant_id ON documents(tenant_id);
CREATE INDEX CONCURRENTLY idx_document_chunks_tenant_id ON document_chunks(tenant_id);
CREATE INDEX CONCURRENTLY idx_queries_tenant_user ON queries(tenant_id, user_id);
CREATE INDEX CONCURRENTLY idx_queries_created_at ON queries(created_at);

-- Optimize PostgreSQL settings
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
```

### Caching Strategy

```python
# Redis caching configuration
CACHING_CONFIG = {
    "embedding_cache_ttl": 3600,  # 1 hour
    "query_cache_ttl": 1800,      # 30 minutes
    "user_session_ttl": 86400,    # 24 hours
}
```

### Load Balancing

```nginx
# nginx load balancing
upstream backend_pool {
    least_conn;
    server backend-1:8000 max_fails=3 fail_timeout=30s;
    server backend-2:8000 max_fails=3 fail_timeout=30s;
    server backend-3:8000 max_fails=3 fail_timeout=30s;
}
```

## Disaster Recovery

### Backup Strategy

1. **Database Backups:**
   - Daily full backups
   - Point-in-time recovery
   - Cross-region replication

2. **Vector Store Backups:**
   - Qdrant snapshots
   - Collection exports
   - Configuration backups

3. **File Storage Backups:**
   - Document files
   - Upload directories
   - Log files

### Recovery Procedures

```bash
# Database recovery
pg_restore -h postgres-host -U rag_user -d multi_tenant_rag backup.sql

# Qdrant recovery
# Restore from snapshot
curl -X POST "http://qdrant:6333/collections/multi_tenant_documents/snapshots/upload" \
     -F "snapshot=@snapshot.tar"
```

## Scaling Considerations

### Horizontal Scaling

1. **Backend Scaling:**
   - Stateless design allows easy horizontal scaling
   - Use load balancers
   - Auto-scaling based on CPU/memory

2. **Database Scaling:**
   - Read replicas for query workloads
   - Connection pooling
   - Partitioning for large datasets

3. **Vector Store Scaling:**
   - Qdrant clustering
   - Collection sharding
   - Distributed search

### Vertical Scaling

Monitor these metrics for scaling decisions:
- CPU utilization > 80%
- Memory usage > 85%
- Disk I/O wait time
- Network bandwidth utilization
- Response times > SLA thresholds

## Troubleshooting

### Common Issues

1. **Database Connection Issues:**
```bash
# Check connectivity
pg_isready -h postgres-host -p 5432 -U rag_user

# Check logs
kubectl logs postgres-0 -n multi-tenant-rag
```

2. **Vector Store Issues:**
```bash
# Health check
curl http://qdrant:6333/health

# Collection status
curl http://qdrant:6333/collections
```

3. **Memory Issues:**
```bash
# Check memory usage
kubectl top pods -n multi-tenant-rag

# Restart if needed
kubectl rollout restart deployment/backend -n multi-tenant-rag
```

### Log Analysis

```bash
# Search for errors
kubectl logs -l app=backend -n multi-tenant-rag | grep ERROR

# Monitor real-time logs
kubectl logs -f deployment/backend -n multi-tenant-rag
```

This deployment guide provides a comprehensive approach to deploying the Multi-Tenant RAG System in production environments. Choose the deployment option that best fits your infrastructure and scaling requirements.