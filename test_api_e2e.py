import asyncio
import httpx
import os
import sys

sys.path.insert(0, os.getcwd())
from dotenv import load_dotenv
load_dotenv(override=True)

API_BASE = "http://localhost:8000/api/v1"

async def main():
    async with httpx.AsyncClient() as client:
        # 1. Auth (Register or Login)
        print("1. Authenticating user...")
        email = "e2e_tester@example.com"
        password = "Password123!"
        
        # Try to register
        res = await client.post(f"{API_BASE}/auth/register", json={"email": email, "password": password})
        if res.status_code == 200:
            token = res.json()["access_token"]
            print("   Registered successfully.")
        else:
            # Maybe already exists, try login
            res = await client.post(f"{API_BASE}/auth/login", json={"email": email, "password": password})
            res.raise_for_status()
            token = res.json()["access_token"]
            print("   Logged in successfully.")
            
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Create Workspace
        print("2. Creating workspace...")
        res = await client.post(
            f"{API_BASE}/workspaces/",
            json={"name": "E2E Test Workspace", "description": "Verification"},
            headers=headers
        )
        res.raise_for_status()
        workspace_id = res.json()["id"]
        print(f"   Workspace created: {workspace_id}")
        
        # 3. Upload Document
        print("3. Uploading document...")
        file_path = "dummy.pdf"
            
        with open(file_path, "rb") as f:
            files = {"file": (file_path, f, "application/pdf")}
            data = {"workspace_id": workspace_id}
            res = await client.post(f"{API_BASE}/documents/upload", files=files, data=data, headers=headers)
            res.raise_for_status()
            doc_id = res.json()["document_id"]
            print(f"   Document uploaded: {doc_id}")
            
        # 4. Poll Document Status
        print("4. Waiting for background pipeline to complete...")
        while True:
            res = await client.get(f"{API_BASE}/documents/{doc_id}", headers=headers)
            res.raise_for_status()
            status = res.json()["status"]
            print(f"   Status: {status}")
            if status == "COMPLETED":
                print("   Pipeline finished successfully!")
                break
            elif status == "FAILED" or status == "GRAPH_EXTRACTION_FAILED":
                print(f"   Pipeline failed! Status: {status}")
                sys.exit(1)
            await asyncio.sleep(5)
            
        # 5. Query
        print("5. Running RAG Query...")
        query_payload = {
            "workspace_id": workspace_id,
            "message": "What is the Hybrid GraphRAG architecture?"
        }
        res = await client.post(f"{API_BASE}/chat/query", json=query_payload, headers=headers)
        res.raise_for_status()
        answer = res.json()["answer"]
        print("\n=== LLM Response ===")
        print(answer)
        print("====================")
        print("\nE2E API VERIFICATION SUCCESSFUL")

if __name__ == "__main__":
    asyncio.run(main())
