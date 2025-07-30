import os
from typing import Any, Dict

import httpx
from babel import Locale

from src.tracing.async_trace import async_airtel_trace
from src.utils.location import get_location_data


@async_airtel_trace
async def transaction_enquiry(
        access_token: str,
        transaction_id: str,
        country: str | None = None,
        currency: str | None = None,
) -> Dict[str, Any]:
    """
    This gets the status of the enquired transaction.
    Args:
        country: The country in which the transaction was performed. If not provided, it will be determined from the location.
        currency: The currency in which the transaction was performed. If not provided, it will be determined from the location and country.
        access_token: The access token generated for the user
        transaction_id: The id of the transaction to be enquired

    Returns:
        Dict[str, Any]: Response that shows information on the transaction being queried

    """
    # Validate whether all the arguments are passed
    if not all([access_token, transaction_id]):
        return {"error": "Missing required arguments"}

    environment_status = os.getenv("PROJECT_ENVIRONMENT", "development")
    base_url = os.getenv("AIRTEL_BASE_URL") \
        if environment_status == "production" \
        else os.getenv("AIRTEL_TEST_BASE_URL")

    # Get the country and currency if not passed
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

    # Get the transaction information
    headers = {
        "Accept": "*/*",
        "X-Country": country,
        "X-Currency": currency,
        "Authorization": f"Bearer {access_token}"
    }

    url = f"{base_url}/standard/v1/payments/{transaction_id}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": "HTTP Error", "details": e.response.text}
        except Exception as e:
            return {"error": f"Transaction Enquiry failed: {e}"}