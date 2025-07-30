import json

from mcp.server.fastmcp import Context
from typing import Dict, Any, Coroutine

from src.servers.airtel.core.collections.ussd_push import ussd_push
from src.servers.airtel.models.context import AirtelContext
from src.servers.airtel.utils.auth import get_access_token


class AirtelTools:
    def __init__(self, mcp) -> None:
        """
        Initializes AirtelTools and registers available tools.
        Args:
            mcp: The MCP server instance to register the tools with.
        """
        self.mcp = mcp

        # Register tools during initialization
        self.register_tools()

    def register_tools(self):
        """
        Register Available Tools
        Returns:

        """
        # Payments - USSD Push
        @self.mcp.tool()
        async def stk_push(
                ctx: Context,
                phone_number: str,
                amount: int,
        ) -> dict[str, str] | str | Coroutine[Any, Any, AirtelContext]:
            try:
                airtel_ctx: AirtelContext = ctx.request_context.lifespan_context

                context = await get_access_token()
                # if not airtel_ctx or not airtel_ctx.access_token:
                #     raise ValueError("Airtel access token is not available. Please authenticate first.")
                return context.access_token

                # Call the function that initiates the USSD Push and get the response
                response = await ussd_push(
                    context.access_token,
                    phone_number,
                    amount,
                )

                return json.dumps(response, indent=2)
            except Exception as e:
                return {"error": f"Failed to initiate Airtel USSD Push: {str(e)}"}
                