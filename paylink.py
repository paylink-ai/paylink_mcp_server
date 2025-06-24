import os
import time
import asyncio
import json
import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response

from src.servers.mpesa.utils.auth import get_access_token
from src.servers.mpesa.models.context import MPesaContext
from src.servers.mpesa.tools.mpesa_tools import MpesaTools


logger = logging.getLogger(__name__)

# Load env
load_dotenv(override=True)




# Create an instance of the MCP server with a lifespan context
mcp = FastMCP(
    "PayLink_MCP_server",
    host="0.0.0.0",
    port=8050,
    stateless_http=True
)

@mcp.custom_route("/mpesa/callback", methods=["POST"])
async def mpesa_callback_handler(request: Request) -> Response:
    """
    Handle M-Pesa webhook callback.
    """
    try:
        # Read the request body (asynchronous)
        body = await request.body()
        logger.info(f"Received M-Pesa webhook: {body}")

        # Parse the JSON payload (M-Pesa sends JSON data)
        payload = json.loads(body.decode("utf-8"))
        
        # Process the M-Pesa payload (add your logic here)
        # Example: Log the transaction details
        logger.info(f"M-Pesa Payload: {payload}")

        # Return a 200 OK response to acknowledge receipt
        return Response(status_code=200, content="Webhook received successfully")
    
    except Exception as e:
        # Log the error for debugging
        logger.error(f"Unexpected error: {e}")
        # Return a 500 error response to M-Pesa
        return Response(status_code=500, content=f"Error processing webhook: {str(e)}")


MpesaTools(mcp=mcp)

# Entry point to start the MCP server
if __name__ == "__main__":

    # mcp.run(transport="stdio")
    mcp.run(transport="streamable-http")
