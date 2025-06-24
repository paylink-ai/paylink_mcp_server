import os
import base64
import httpx
import asyncio
import time
from dotenv import load_dotenv
from starlette.requests import Request
from mcp.server.fastmcp import Context
from src.servers.mpesa.models.context import MPesaContext

load_dotenv(override=True)

async def get_access_token(ctx: Context) -> MPesaContext:
    """
    Helper method to retrieve access token and extract M-Pesa headers
    """
    request: Request = ctx.request_context.request

    consumer_key = request.headers.get("mpesa_consumer_key")
    consumer_secret = request.headers.get("mpesa_consumer_secret")
    base_url = request.headers.get("mpesa_base_url")

    access_token_response = await generate_access_token(consumer_key, consumer_secret, base_url)
    
    # Extract the actual token from the response
    token_value = access_token_response.get("access_token")
    # Extract and normalize M-Pesa headers
    mpesa_headers = {}
    for key, value in request.headers.items():
        if key.lower().startswith("mpesa_"):
            mpesa_headers[key.upper()] = value
        elif key.lower().startswith("mpesa"):
            formatted_key = f"MPESA_{key.upper()[5:]}"
            mpesa_headers[formatted_key] = value

    # Create and return the context
    return MPesaContext(access_token=token_value, headers=mpesa_headers)


async def generate_access_token(consumer_key: str, consumer_secret: str, base_url: str):
    
    if not consumer_key or not consumer_secret or not base_url:
        raise ValueError("Missing M-Pesa environment variables.")

    auth_string = f"{consumer_key}:{consumer_secret}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()

    # Fix the URL path - ensure it's correctly formatted
    url = f"{base_url.rstrip('/')}/oauth/v1/generate"
    headers = {"Authorization": f"Basic {encoded_auth}"}
    params = {"grant_type": "client_credentials"}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            return {
                "access_token": data["access_token"],
                "expires_in": int(data["expires_in"]),
            }
    except httpx.HTTPStatusError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        print(f"Error getting access token: {str(e)}")
        raise