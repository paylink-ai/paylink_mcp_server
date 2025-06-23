import requests

async def get_location_data(ip: str = None):
    try:
        response = requests.get("https://ipapi.co/json/" if ip is None else f"https://ipapi.co/{ip}/json/")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        return None