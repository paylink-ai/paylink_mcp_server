import asyncio
import os
import time
import httpx
from dotenv import load_dotenv
from src.servers.airtel.models.context import AirtelContext

load_dotenv(override=True)


async def get_access_token():
    environment_status = os.getenv("PROJECT_ENVIRONMENT", "development")
    client_id = os.getenv("AIRTEL_CLIENT_ID")
    client_secret = os.getenv("AIRTEL_CLIENT_SECRET")
    base_url = os.getenv("AIRTEL_BASE_URL") \
        if environment_status == "production" \
        else os.getenv("AIRTEL_TEST_BASE_URL")

    if not client_id or not client_secret or not base_url:
        raise ValueError("Missing Airtel environment variables.")

    url = f"{base_url}/auth/oauth2/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "*/*"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return {
            "access_token": data["access_token"],
            "expires_in": int(data["expires_in"]),
            "token_type": data["token_type"]
        }

async def refresh_access_token(context: AirtelContext):
    while True:
        sleep_for = max(context.expires_at - time.time() - 60, 60)
        await asyncio.sleep(sleep_for)
        try:
            print("Refreshing Airtel access token...")
            token_data = await get_access_token()
            context.access_token = token_data["access_token"]
            context.expires_at = time.time() + token_data["expires_in"]
        except Exception as e:
            print(f"Token refresh failed: {e}")
            await asyncio.sleep(30)