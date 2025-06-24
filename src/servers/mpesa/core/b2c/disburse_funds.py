import os
import httpx
import time
from typing import Dict, Any
from src.tracing.async_trace import async_trace

@async_trace
async def disburse_funds(
    access_token: str,
    phone_number: str,
    amount: int,
    remarks: str,
    occasion: str = ""
) -> Dict[str, Any]:
    """
    Initiates an M-Pesa B2C (Business to Customer) payment.

    This allows a business to send money directly to a customer via M-Pesa. Examples include salary disbursements, withdrawals, or promotions.

    Args:
        access_token (str): The access token for authenticating with the M-Pesa API.
        phone_number (str): The recipient’s phone number in the format 2547XXXXXXXX.
        amount (int): The amount to be disbursed.
        remarks (str): A brief note or reason for the disbursement.
        occasion (str, optional): Optional field for specifying the occasion, e.g., "Bonus", "Salary".

    Returns:
        Dict[str, Any]: JSON response from M-Pesa B2C API or an error object.
    """

    shortcode = os.getenv("B2C_SHORTCODE")
    initiator_name = os.getenv("B2C_INITIATOR_NAME")
    security_credential = os.getenv("B2C_SECURITY_CREDENTIAL")
    callback_url = os.getenv("B2C_CALLBACK_URL")
    base_url = os.getenv("BASE_URL")

    if not all([shortcode, initiator_name, security_credential, callback_url, base_url]):
        return {"error": "Missing B2C environment variables"}

    if not phone_number.startswith("254") or len(phone_number) != 12:
        return {"error": "Invalid phone number format. Must be 254XXXXXXXXX"}

    payload = {
        "InitiatorName": initiator_name,
        "SecurityCredential": security_credential,
        "CommandID": "BusinessPayment",  # Alternatives: SalaryPayment, PromotionPayment
        "Amount": amount,
        "PartyA": shortcode,
        "PartyB": phone_number,
        "Remarks": remarks,
        "QueueTimeOutURL": callback_url,
        "ResultURL": callback_url,
        "Occasion": occasion
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/mpesa/b2c/v3/paymentrequest"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": "HTTP Error", "details": e.response.text}
        except Exception as e:
            return {"error": f"B2C Payment failed: {e}"}
