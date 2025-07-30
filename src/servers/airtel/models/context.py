import asyncio
from dataclasses import dataclass


@dataclass
class AirtelContext:
    """Context for managing Airtel Integration"""
    access_token: str
    expires_at: float
    refresh_task: asyncio.Task | None