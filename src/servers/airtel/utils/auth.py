import asyncio
import os
import time
from typing import Any, Coroutine

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import Context
from starlette.requests import Request

from src.servers.airtel.models.context import AirtelContext

load_dotenv(override=True)


async def get_access_token() -> AirtelContext:

    """
    Helper method to retrieve access token for Airtel services.
    Args:
        ctx:

    Returns:

    """
    # request: Request = ctx.request_context.request

    environment_status = os.getenv("PROJECT_ENVIRONMENT", "development")
    # client_id = request.headers.get("airtel_client_id")
    client_id = os.getenv("AIRTEL_CLIENT_ID")
    # client_secret = request.headers.get("airtel_client_secret")
    client_secret = os.getenv("AIRTEL_CLIENT_SECRET")
    base_url = os.getenv("AIRTEL_BASE_URL") \
        if environment_status == "production" \
        else os.getenv("AIRTEL_TEST_BASE_URL")

    if not client_id or not client_secret or not base_url:
        raise ValueError("Missing Airtel environment variables.")

    token_data = await generate_access_token(client_id, client_secret, base_url)

    return AirtelContext(access_token=token_data.get("access_token"), expires_at=token_data.get("expires_in") + time.time(), refresh_task=None)

async def generate_access_token(client_id: str, client_secret: str, base_url: str) -> dict[str, int | Any]:
    """
    Generate an access token for Airtel services.
    Args:
        client_id: The client ID for Airtel API.
        client_secret: The client secret for Airtel API.
        base_url: The base URL for Airtel API.

    Returns:
        A dictionary containing the access token and its expiration time.
    """
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

# async def refresh_access_token(context: AirtelContext):
#     while True:
#         sleep_for = max(context.expires_at - time.time() - 60, 60)
#         await asyncio.sleep(sleep_for)
#         try:
#             print("Refreshing Airtel access token...")
#             token_data = await get_access_token(ctx=Context(request_context=context.request_context))
#             context.access_token = token_data["access_token"]
#             context.expires_at = time.time() + token_data["expires_in"]
#         except Exception as e:
#             print(f"Token refresh failed: {e}")
#             await asyncio.sleep(30)