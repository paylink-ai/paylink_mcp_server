import os
import httpx
import json
from typing import Dict, Any

async def generate_dynamic_qr(access_token: str, payload: Dict, headers: Dict = None) -> Dict[str, Any]:
    # Get base_url from headers if available
    base_url = headers.get("MPESA_BASE_URL") if headers else None
    
    # Fall back to environment variable if not in headers
    if not base_url:
        base_url = os.getenv("BASE_URL")
        
    if not base_url:
        raise ValueError("Missing base URL for M-Pesa API")
    
    # Ensure the base_url is properly formatted
    base_url = base_url.rstrip('/')
    url = f"{base_url}/mpesa/qrcode/v1/generate"
    
    # Validate required payload fields
    required_fields = ["MerchantName", "RefNo", "Amount", "TrxCode", "CPI"]
    for field in required_fields:
        if field not in payload or not payload[field]:
            return {"error": f"Missing required field: {field}"}
    
    # Ensure Amount is an integer
    if not isinstance(payload["Amount"], int):
        try:
            payload["Amount"] = int(payload["Amount"])
        except (ValueError, TypeError):
            return {"error": "Amount must be an integer"}
    
    # Ensure Size is a string
    if "Size" in payload and not isinstance(payload["Size"], str):
        payload["Size"] = str(payload["Size"])

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP Error: {e.response.status_code}"
        try:
            error_data = e.response.json()
            if isinstance(error_data, dict):
                error_msg = f"{error_msg} - {json.dumps(error_data)}"
        except Exception:
            if e.response.text:
                error_msg = f"{error_msg} - {e.response.text}"
        return {"error": error_msg}
    except Exception as e:
        return {"error": f"Failed to generate QR code: {str(e)}"}
