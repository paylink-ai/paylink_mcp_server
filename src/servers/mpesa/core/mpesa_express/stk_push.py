import os
import time
import httpx
import base64
from typing import Dict, Any
from paylink_tracing.trace import async_trace

from dotenv import load_dotenv
load_dotenv(override=True)

# @async_trace
async def initiate_stk_push(
    access_token: str,  # Changed from Dict to str
    phone_number: str,  
    amount: int,
    account_reference: str,
    transaction_desc: str,
    transaction_type: str,
    headers: Dict[str, str] = None,
) -> Dict[str, Any]:
    """
    Initiates an M-Pesa STK Push (Sim Tool Kit) transaction, which allows a merchant to request a customer to authorize a payment through M-Pesa.

    This tool triggers the M-Pesa Lipa na M-Pesa Online API (STK Push), which sends a payment request to the customer's M-Pesa registered phone number.
    The customer receives a prompt on their phone to enter their M-Pesa PIN to authorize and complete the payment.

    Args:
        phone_number (str): The mobile number to which the STK Push prompt will be sent (should be an M-Pesa registered number).
        amount (int): The amount to be paid, in integer value.
        account_reference (str): A reference string for the account being charged, displayed to the customer in the STK prompt.
        transaction_desc (str): A brief description of the transaction, displayed in the STK prompt.
        transaction_type (str): The type of transaction being processed (e.g., "CustomerPayBillOnline" for pay bill transactions, or "CustomerBuyGoodsOnline" for goods purchases).

    Returns:
        Dict[str, Any]: A JSON object containing the result of the request. On success, includes the transaction's status and details. In case of failure, an error message will be returned.

    """
    # Initialize variables to avoid UnboundLocalError
    business_shortcode = None
    passkey = None
    callback_url = None
    base_url = None
    
    # Get values from headers if provided
    if headers:
        business_shortcode = headers.get("MPESA_BUSINESS_SHORTCODE")
        passkey = headers.get("MPESA_PASSKEY")
        callback_url = headers.get("MPESA_CALLBACK_URL")
        base_url = headers.get("MPESA_BASE_URL")

    
    if not all([business_shortcode, passkey, callback_url, base_url]):
        return {"error": "Missing M-Pesa STK configuration"}

    if not phone_number.startswith("254") or len(phone_number) != 12:
        return {"error": "Invalid phone number format. Must be 254XXXXXXXXX"}

    if len(account_reference) > 12:
        return {"error": "Account reference must be ≤ 12 characters"}

    if len(transaction_desc) > 13:
        return {"error": "Transaction description must be ≤ 13 characters"}

    VALID_TRANSACTION_TYPES = {"CustomerPayBillOnline", "CustomerBuyGoodsOnline"}

    if transaction_type not in VALID_TRANSACTION_TYPES:
        return {
            "error": f"Invalid transaction type {', '.join(VALID_TRANSACTION_TYPES)}"
        }

    timestamp = time.strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(
        f"{business_shortcode}{passkey}{timestamp}".encode()
    ).decode()

    payload = {
        "BusinessShortCode": business_shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": transaction_type,
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": business_shortcode,
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url,
        "AccountReference": account_reference,
        "TransactionDesc": transaction_desc,
    }

    # Use the access token directly since it's now passed as a string
    if not access_token:
        return {"error": "Invalid access token"}
        
    request_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # Ensure base_url is properly formatted
    url = f"{base_url.rstrip('/')}/mpesa/stkpush/v1/processrequest"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=request_headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            return {"error": "HTTP Error", "details": e.response.text}
        except Exception as e:
            print(f"STK Push failed: {str(e)}")
            return {"error": f"STK Push failed: {str(e)}"}
