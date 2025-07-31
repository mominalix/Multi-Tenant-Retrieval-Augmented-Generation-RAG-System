# API Reference

This document provides detailed information about the Multi-Tenant RAG System API endpoints.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All protected endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Error Responses

All endpoints may return the following error responses:

```json
{
  "detail": "Error message",
  "status_code": 400
}
```

Common HTTP status codes:
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## Authentication Endpoints

### POST /auth/login

Authenticate user and get JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "tenant_identifier": "acme" // optional: subdomain or tenant ID
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "user",
    "role": "user",
    "is_active": true,
    "created_at": "2024-01-01T12:00:00Z",
    "tenant_id": "uuid"
  },
  "tenant": {
    "id": "uuid",
    "name": "Acme Corporation",
    "subdomain": "acme",
    "llm_provider": "openai",
    "llm_model": "gpt-3.5-turbo"
  }
}
```

### POST /auth/register

Register a new user in a tenant.

**Query Parameters:**
- `tenant_id` (required): The tenant ID to register the user in

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "username": "newuser",
  "password": "password123",
  "role": "user"
}
```

**Response:**
```json
{
  "id": "uuid",
  "email": "newuser@example.com",
  "username": "newuser",
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-01T12:00:00Z",
  "tenant_id": "uuid"
}
```

### GET /auth/me

Get current authenticated user information.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "user",
  "role": "user",
  "is_active": true,
  "last_login": "2024-01-01T12:00:00Z",
  "created_at": "2024-01-01T11:00:00Z",
  "tenant_id": "uuid"
}
```

## Tenant Management (Admin Only)

### POST /auth/tenants

Create a new tenant.

**Headers:** `Authorization: Bearer <admin-token>`

**Request Body:**
```json
{
  "name": "New Company",
  "subdomain": "newcompany",
  "llm_provider": "openai",
  "llm_model": "gpt-4"
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "New Company",
  "subdomain": "newcompany",
  "llm_provider": "openai",
  "llm_model": "gpt-4",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "max_documents": 1000,
  "max_queries_per_day": 10000,
  "is_active": true,
  "created_at": "2024-01-01T12:00:00Z"
}
```

### GET /auth/tenants

List all tenants.

**Headers:** `Authorization: Bearer <admin-token>`

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 100)

## Document Management

### POST /documents/upload

Upload a document for processing.

**Headers:** `Authorization: Bearer <token>`

**Request:** Multipart form data
- `file`: The document file (PDF, TXT, or DOCX)
- `metadata` (optional): JSON string with additional metadata

**Example metadata:**
```json
{
  "title": "Company Handbook",
  "category": "HR",
  "description": "Employee guidelines and policies",
  "tags": ["hr", "handbook", "policies"]
}
```

**Response:**
```json
{
  "id": "uuid",
  "filename": "stored_filename.pdf",
  "original_filename": "handbook.pdf",
  "content_type": "application/pdf",
  "file_size": 1048576,
  "status": "uploaded",
  "total_chunks": 0,
  "processed_chunks": 0,
  "uploaded_at": "2024-01-01T12:00:00Z",
  "created_at": "2024-01-01T12:00:00Z"
}
```

### GET /documents/

List documents for the current tenant.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 20)
- `status_filter` (optional): Filter by document status

**Response:**
```json
{
  "documents": [
    {
      "id": "uuid",
      "filename": "stored_filename.pdf",
      "original_filename": "handbook.pdf",
      "status": "processed",
      "total_chunks": 25,
      "processed_chunks": 25,
      "word_count": 5000,
      "uploaded_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20,
  "pages": 1
}
```

### GET /documents/{document_id}

Get details of a specific document.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "filename": "stored_filename.pdf",
  "original_filename": "handbook.pdf",
  "content_type": "application/pdf",
  "file_size": 1048576,
  "status": "processed",
  "total_chunks": 25,
  "processed_chunks": 25,
  "title": "Company Handbook",
  "language": "en",
  "word_count": 5000,
  "collection_name": "multi_tenant_documents",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "metadata": {
    "category": "HR",
    "description": "Employee guidelines"
  },
  "tags": ["hr", "handbook"],
  "uploaded_at": "2024-01-01T12:00:00Z",
  "processed_at": "2024-01-01T12:01:00Z",
  "created_at": "2024-01-01T12:00:00Z"
}
```

### DELETE /documents/{document_id}

Delete a document and all associated data.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "message": "Document deleted successfully"
}
```

## RAG Queries

### POST /queries/rag

Submit a RAG query and get a response.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "query": "What is the company's vacation policy?",
  "max_chunks": 5,
  "score_threshold": 0.7,
  "document_ids": ["uuid1", "uuid2"], // optional
  "tags": ["hr", "policies"], // optional
  "llm_provider": "openai", // optional
  "llm_model": "gpt-4", // optional
  "temperature": 0.7,
  "max_tokens": 1000,
  "system_prompt": "You are a helpful HR assistant.", // optional
  "session_id": "session123", // optional
  "conversation_turn": 1,
  "include_sources": true
}
```

**Response:**
```json
{
  "query_id": "uuid",
  "query": "What is the company's vacation policy?",
  "response": "According to the company handbook, employees are entitled to...",
  "context_documents": [
    {
      "chunk_id": "uuid",
      "document_id": "uuid",
      "score": 0.85,
      "text": "Vacation Policy: All full-time employees...",
      "source": "handbook.pdf",
      "page_number": 12,
      "chunk_index": 0,
      "metadata": {}
    }
  ],
  "context_used": "Combined context from retrieved documents...",
  "processing_time_ms": 1500,
  "llm_provider": "openai",
  "llm_model": "gpt-4",
  "input_tokens": 150,
  "output_tokens": 100,
  "total_tokens": 250,
  "estimated_cost": 0.005,
  "source_attribution": ["handbook.pdf"],
  "contains_citations": true,
  "session_id": "session123",
  "conversation_turn": 1,
  "created_at": "2024-01-01T12:00:00Z"
}
```

### POST /queries/rag/stream

Submit a RAG query and get a streaming response.

**Headers:** `Authorization: Bearer <token>`

**Request Body:** Same as `/queries/rag` with `stream: true`

**Response:** Server-Sent Events (text/plain)
```
data: According
data:  to
data:  the
data:  company
data:  handbook
data: ...
data: [DONE]
```

### GET /queries/history

Get query history for the current user.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 20)
- `session_id` (optional): Filter by session ID

**Response:**
```json
{
  "queries": [
    {
      "id": "uuid",
      "query_text": "What is the vacation policy?",
      "query_type": "rag",
      "status": "completed",
      "processing_time_ms": 1500,
      "total_tokens": 250,
      "created_at": "2024-01-01T12:00:00Z",
      "response": {
        "response_text": "According to the handbook...",
        "confidence_score": 0.85
      }
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20,
  "pages": 1
}
```

### POST /queries/{query_id}/feedback

Submit feedback for a query.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "query_id": "uuid",
  "rating": 5,
  "feedback": "Very helpful response!"
}
```

**Response:**
```json
{
  "message": "Feedback submitted successfully"
}
```

## Analytics

### GET /queries/analytics/summary

Get query analytics for the tenant.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `days` (optional): Number of days to analyze (default: 30)

**Response:**
```json
{
  "tenant_id": "uuid",
  "total_queries": 150,
  "queries_today": 5,
  "avg_processing_time_ms": 1200.5,
  "avg_tokens_per_query": 220.0,
  "total_cost": 15.75,
  "top_query_types": [
    {"type": "rag", "count": 140},
    {"type": "search", "count": 10}
  ],
  "avg_rating": 4.2,
  "period_start": "2024-01-01T00:00:00Z",
  "period_end": "2024-01-31T23:59:59Z"
}
```

## Tenant Information

### GET /tenant/info

Get current tenant information.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": "uuid",
  "name": "Acme Corporation",
  "subdomain": "acme",
  "llm_provider": "openai",
  "llm_model": "gpt-4",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "max_documents": 1000,
  "max_queries_per_day": 10000,
  "is_active": true,
  "created_at": "2024-01-01T12:00:00Z"
}
```

### GET /tenant/stats

Get statistics for the current tenant.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "tenant_id": "uuid",
  "tenant_name": "Acme Corporation",
  "user_count": 25,
  "document_count": 100,
  "processed_document_count": 95,
  "created_at": "2024-01-01T12:00:00Z",
  "is_active": true,
  "configuration": {
    "llm_provider": "openai",
    "llm_model": "gpt-4",
    "max_documents": 1000,
    "max_queries_per_day": 10000
  }
}
```

## Rate Limits

The API implements rate limiting to ensure fair usage:

- **Authentication endpoints**: 10 requests per minute
- **Document upload**: 5 uploads per minute
- **RAG queries**: 60 queries per minute
- **Other endpoints**: 100 requests per minute

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Request limit per window
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Window reset time (Unix timestamp)

## Webhooks (Future Feature)

The system is designed to support webhooks for real-time notifications:

- Document processing completion
- Query completion
- System alerts
- Usage threshold warnings