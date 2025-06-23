import os
from typing import Any, Dict
import locale
from babel import Locale
import httpx
import requests

from src.tracing.async_trace import async_airtel_trace
from src.utils.helpers import random_string
from src.utils.location import get_location_data


@async_airtel_trace
async def ussd_push(
        access_token: str,
        phone_number: str,
        amount: int,
        country: str | None,
        currency: str | None,
        reference: str | None = None,
        reference_id: str | None = None,
) -> Dict[str, Any]:
    """
    Body:
        {
            "reference": "Testing transaction",
            "subscriber": {
                "country": "UG",
                "currency": "UGX",
                "msisdn": "12****89"
            },
            "transaction": {
                "amount": 1000,
                "country": "UG",
                "currency": "UGX",
                "id": "random-unique-id"
            }
        }

    Args:
        reference_id:
        access_token:
        phone_number:
        amount:
        country:
        currency:
        reference:

    Expected Response upon success:
        {
            "data": {
                "transaction": {
                    "id": false,
                    "status": "SUCCESS"
                }
            },
            "status": {
                "code": "200",
                "message": "SUCCESS",
                "result_code": "ESB000010",
                "response_code": "DP00800001006",
                "success": true
            }
        }

    Returns
        Dict[str, Any]: A dictionary containing the response data and status code.

    """

    environment_status = os.getenv("PROJECT_ENVIRONMENT", "development")
    base_url = os.getenv("AIRTEL_BASE_URL") \
        if environment_status == "production" \
        else os.getenv("AIRTEL_TEST_BASE_URL")
    
    # Validate whether all the arguments are passed
    if not all([access_token, phone_number, amount, country, currency]):
        return {"error": "Missing required arguments"}

    # Get the current country of location if not passed
    location = await get_location_data()

    if country and not currency:
        try:
            locale_obj = Locale.parse(f"und_{country}")
            currency = locale_obj.currency
            if not currency:
                return {"error": f"Could not determine currency for country code: {country}"}
        except Exception:
            return {"error": f"Invalid country code: {country}"}

    if not country:
        country = location.get("country")
        currency = location.get("currency")

    if not country or not currency:
        return {
            "error": "Country or Currency could not be determined. Please provide them as arguments or in the environment variables."
        }

    # Clean the phone number. Ensure that it does not have the preceding country code
    if phone_number.startswith("0"):
        return {
            "error": "Phone number must not start with 0. Please remove the leading 0."
        }

    if phone_number.startswith(location.get("country_calling_code")) \
            or phone_number.startswith(location.get("country_calling_code")[1:]):
        return {
            "error": "Phone number must not start with the country calling code. Please remove the leading country calling code."
        }

    payload = {
        "reference": reference if reference is not None else "Testing transaction",
        "subscriber": {
            "country": country,
            "currency": currency,
            "msisdn": phone_number
        },
        "transaction": {
            "amount": amount,
            "country": country,
            "currency": currency,
            "id": reference_id if reference_id is not None else random_string(8)
        }
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Country": country,
        "X-Currency": currency,
        "Authorization": f"Bearer {access_token}"
    }

    url = f"{base_url}/merchant/v2/payments"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": "HTTP Error", "details": e.response.text}
        except Exception as e:
            return {"error": f"USSD Push failed: {e}"}