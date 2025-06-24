from dataclasses import dataclass, field
import asyncio
from typing import Dict, Any, Optional

@dataclass
class MPesaContext:
    """Context for managing MPesa Integration"""
    access_token: Dict[str, Any] = None  # Changed to Dict to handle the full response
    expires_at: float = 0
    refresh_task: Optional[asyncio.Task] = None
    headers: Dict[str, str] = field(default_factory=dict)  # Added headers field
