import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from supabase import create_client, Client

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_SERVICE_KEY")

supabase: Client = create_client(url, key)

async def confirm_all_users():
    try:
        print("Fetching users...")
        users = supabase.auth.admin.list_users()
        
        for user in users.users:
            if not user.email_confirmed_at:
                print(f"Confirming user: {user.email}")
                supabase.auth.admin.update_user_by_id(
                    user.id, 
                    attributes={"email_confirm": True}
                )
        print("All users confirmed successfully.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(confirm_all_users())
