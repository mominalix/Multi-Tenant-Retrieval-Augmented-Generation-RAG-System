#!/usr/bin/env python3
"""
Setup script for creating sample tenants and users
Run this script after the application is up and running
"""
import asyncio
import requests
import json
import sys
from pathlib import Path

# API configuration
API_BASE_URL = "http://localhost:8000/api/v1"

# Sample data
SAMPLE_TENANTS = [
    {
        "name": "Acme Corporation",
        "subdomain": "acme",
        "llm_provider": "openai",
        "llm_model": "gpt-3.5-turbo"
    },
    {
        "name": "TechStart Inc",
        "subdomain": "techstart", 
        "llm_provider": "openai",
        "llm_model": "gpt-4"
    }
]

SAMPLE_USERS = [
    {
        "email": "admin@acme.com",
        "username": "acme_admin",
        "password": "admin123",
        "role": "admin"
    },
    {
        "email": "user@acme.com", 
        "username": "acme_user",
        "password": "user123",
        "role": "user"
    },
    {
        "email": "admin@techstart.com",
        "username": "techstart_admin", 
        "password": "admin123",
        "role": "admin"
    }
]


class SetupClient:
    """Client for setting up sample data"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.admin_token = None
    
    def wait_for_api(self, max_retries: int = 30):
        """Wait for API to be available"""
        for i in range(max_retries):
            try:
                response = self.session.get(f"{self.base_url}/../health")
                if response.status_code == 200:
                    print("✅ API is available")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            print(f"⏳ Waiting for API... (attempt {i+1}/{max_retries})")
            import time
            time.sleep(2)
        
        return False
    
    def create_admin_user(self) -> bool:
        """Create initial admin user"""
        # For the first setup, we need to manually create an admin user
        # This would typically be done through database seeding or a special endpoint
        print("ℹ️  Note: You need to create the first admin user manually through the database")
        print("   or implement a special admin creation endpoint")
        return True
    
    def login_as_admin(self, email: str, password: str) -> bool:
        """Login as admin user"""
        try:
            response = self.session.post(f"{self.base_url}/auth/login", json={
                "email": email,
                "password": password
            })
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                print(f"✅ Logged in as admin: {email}")
                return True
            else:
                print(f"❌ Failed to login as admin: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Login failed: {e}")
            return False
    
    def create_tenant(self, tenant_data: dict) -> dict:
        """Create a new tenant"""
        try:
            response = self.session.post(f"{self.base_url}/auth/tenants", json=tenant_data)
            
            if response.status_code == 200:
                tenant = response.json()
                print(f"✅ Created tenant: {tenant['name']} (ID: {tenant['id']})")
                return tenant
            else:
                print(f"❌ Failed to create tenant {tenant_data['name']}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Tenant creation failed: {e}")
            return None
    
    def create_user(self, user_data: dict, tenant_id: str) -> dict:
        """Create a new user"""
        try:
            response = self.session.post(
                f"{self.base_url}/auth/register",
                json=user_data,
                params={"tenant_id": tenant_id}
            )
            
            if response.status_code == 200:
                user = response.json()
                print(f"✅ Created user: {user['email']} in tenant {tenant_id}")
                return user
            else:
                print(f"❌ Failed to create user {user_data['email']}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ User creation failed: {e}")
            return None
    
    def create_sample_document(self, tenant_id: str, user_email: str, user_password: str):
        """Create a sample document"""
        try:
            # Login as user
            login_response = self.session.post(f"{self.base_url}/auth/login", json={
                "email": user_email,
                "password": user_password,
                "tenant_identifier": tenant_id
            })
            
            if login_response.status_code != 200:
                print(f"❌ Failed to login as user for document upload")
                return
            
            user_token = login_response.json()["access_token"]
            user_session = requests.Session()
            user_session.headers.update({"Authorization": f"Bearer {user_token}"})
            
            # Create sample document content
            sample_content = """
# Sample Company Document

## About Our Company
Our company has been providing innovative solutions for over 10 years. We specialize in technology consulting and software development.

## Services
- Software Development
- Cloud Solutions
- Data Analytics
- AI/ML Consulting

## Contact Information
Email: info@company.com
Phone: +1 (555) 123-4567
Address: 123 Tech Street, Silicon Valley, CA 94000

## Mission Statement
To deliver cutting-edge technology solutions that drive business success and innovation.
            """.strip()
            
            # Upload document
            files = {
                "file": ("sample_document.txt", sample_content, "text/plain")
            }
            data = {
                "metadata": json.dumps({
                    "title": "Sample Company Document",
                    "category": "General",
                    "description": "A sample document for testing the RAG system",
                    "tags": ["sample", "company", "info"]
                })
            }
            
            response = user_session.post(f"{self.base_url}/documents/upload", files=files, data=data)
            
            if response.status_code == 200:
                doc = response.json()
                print(f"✅ Created sample document: {doc['original_filename']} (ID: {doc['id']})")
            else:
                print(f"❌ Failed to upload sample document: {response.text}")
                
        except Exception as e:
            print(f"❌ Sample document creation failed: {e}")


def main():
    """Main setup function"""
    print("🚀 Setting up Multi-Tenant RAG System sample data")
    print("=" * 50)
    
    client = SetupClient(API_BASE_URL)
    
    # Wait for API to be available
    if not client.wait_for_api():
        print("❌ API is not available. Please ensure the backend is running.")
        sys.exit(1)
    
    print("\n📋 Setup Instructions:")
    print("1. This script will help you create sample tenants and users")
    print("2. You need to have admin access to create tenants")
    print("3. Make sure you have set up your API keys in the environment")
    
    # Get admin credentials
    print("\n🔑 Admin Login Required")
    admin_email = input("Enter admin email (or press Enter to skip): ").strip()
    
    if not admin_email:
        print("ℹ️  Skipping automated setup. You can create tenants manually through the API.")
        return
    
    admin_password = input("Enter admin password: ").strip()
    
    if not client.login_as_admin(admin_email, admin_password):
        print("❌ Cannot proceed without admin access")
        return
    
    print("\n🏢 Creating sample tenants...")
    created_tenants = []
    
    for tenant_data in SAMPLE_TENANTS:
        tenant = client.create_tenant(tenant_data)
        if tenant:
            created_tenants.append(tenant)
    
    print(f"\n👥 Creating sample users...")
    
    # Create users for each tenant
    for i, tenant in enumerate(created_tenants):
        # Create admin user for tenant
        admin_user_data = SAMPLE_USERS[i * 2] if i * 2 < len(SAMPLE_USERS) else SAMPLE_USERS[0]
        client.create_user(admin_user_data, tenant["id"])
        
        # Create regular user for tenant if available
        if (i * 2 + 1) < len(SAMPLE_USERS):
            user_data = SAMPLE_USERS[i * 2 + 1]
            client.create_user(user_data, tenant["id"])
            
            # Create sample document
            print(f"\n📄 Creating sample document for {tenant['name']}...")
            client.create_sample_document(tenant["id"], user_data["email"], user_data["password"])
    
    print("\n✅ Setup completed successfully!")
    print("\n📋 Summary:")
    print(f"   Created {len(created_tenants)} tenants")
    print(f"   Frontend URL: http://localhost:8501")
    print(f"   API Documentation: http://localhost:8000/docs")
    
    print("\n🔑 Sample Login Credentials:")
    for i, tenant in enumerate(created_tenants):
        if i * 2 < len(SAMPLE_USERS):
            user = SAMPLE_USERS[i * 2]
            print(f"   Tenant: {tenant['name']} ({tenant['subdomain']})")
            print(f"   Email: {user['email']}")
            print(f"   Password: {user['password']}")
            print()


if __name__ == "__main__":
    main()