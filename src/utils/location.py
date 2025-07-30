import httpx

async def get_location_data(ip: str = None):
    async with httpx.AsyncClient() as client:
        try:
            url = "https://ipapi.co/json/" if ip is None else f"https://ipapi.co/{ip}/json/"
            response = await client.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            return None
