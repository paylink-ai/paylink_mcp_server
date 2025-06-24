import os
import time
import base64
import httpx
from typing import Dict, Any

async def query_stk_push_status(
    access_token: str,
    checkout_request_id: str,
    headers: Dict[str, str] = None
) -> Dict[str, Any]:
    """
    Queries the status of a previously initiated M-Pesa STK Push transaction.

    Args:
        access_token (str): OAuth access token for M-Pesa API.
        checkout_request_id (str): Unique CheckoutRequestID received after initiating STK push.

    Returns:
        Dict[str, Any]: A JSON object containing the result of the query. Includes ResultCode and status description.
    """

    # Get business shortcode and passkey from headers if available, otherwise from env vars
    business_shortcode = headers.get("MPESA_BUSINESS_SHORTCODE") if headers else None
    passkey = headers.get("MPESA_PASSKEY") if headers else None
    base_url = headers.get("MPESA_BASE_URL") if headers else None
    
    # Fallback to environment variables if not in headers
    if not business_shortcode:
        business_shortcode = os.getenv("BUSINESS_SHORTCODE")
    if not passkey:
        passkey = os.getenv("PASSKEY")
    if not base_url:
        base_url = os.getenv("BASE_URL")

    if not all([business_shortcode, passkey, base_url]):
        return {"error": "Missing M-Pesa environment variables"}

    timestamp = time.strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(
        f"{business_shortcode}{passkey}{timestamp}".encode()
    ).decode()

    payload = {
        "BusinessShortCode": business_shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "CheckoutRequestID": checkout_request_id
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/mpesa/stkpushquery/v1/query"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": "HTTP Error", "details": e.response.text}
        except Exception as e:
            return {"error": f"Query failed: {e}"}
