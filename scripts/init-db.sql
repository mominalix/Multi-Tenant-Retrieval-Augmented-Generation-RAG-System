-- Initialize Multi-Tenant RAG Database
-- This script sets up the basic database configuration

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schema for the application
CREATE SCHEMA IF NOT EXISTS multi_tenant_rag;

-- Set default search path
SET search_path TO multi_tenant_rag, public;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA multi_tenant_rag TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA multi_tenant_rag TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA multi_tenant_rag TO postgres;