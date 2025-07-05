import functools
import inspect
import time
import os
from datetime import datetime
from typing import Any, Callable
import httpx
from dotenv import load_dotenv
import uuid
from starlette.requests import Request
from mcp.server.fastmcp import Context

load_dotenv(override=True)

# FastAPI endpoint URL (adjust as needed)
TRACE_ENDPOINT_URL = "http://localhost:8000/api/v1/trace"

def async_trace(func: Callable):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        func_name = func.__name__

        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        arguments = bound_args.arguments
        
        request: Request = kwargs.get("ctx").request_context.request

        paylink_api_key = request.headers.get("paylink_api_key")
        paylink_project = request.headers.get("paylink_project")
        

        trace_id = str(uuid.uuid4())
        trace_data = {
            "trace_id": trace_id,
            "user_api_key": paylink_api_key,
            "project_name": paylink_project,
            "payment_provider": "M-Pesa",
            "function_name": func_name,
            "timestamp": datetime.now().isoformat(),
            "input_data": str(arguments),
        }

        try:
            result = await func(*args, **kwargs)

            trace_data.update({
                "status": "error" if isinstance(result, dict) and "error" in result else "success",
                "latency": round(time.time() - start_time, 3),
                "error_message": result.get("error") if isinstance(result, dict) and "error" in result else None,
                "output_data": str(result),
            })
            return result
        except Exception as e:
            trace_data.update({
                "status": "error",
                "latency": round(time.time() - start_time, 3),
                "error_message": str(e),
            })
            raise
        finally:
            async with httpx.AsyncClient() as client:
                await client.post(TRACE_ENDPOINT_URL, json=trace_data)

    return wrapper

def async_airtel_trace(func: Callable):
    @functools.wraps(func)
    async def airtel_wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        func_name = func.__name__

        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        arguments = bound_args.arguments

        transaction_context = {
            "phone_number": arguments.get("phone_number"),
            "amount": arguments.get("amount"),
            "account_reference": arguments.get("account_reference"),
            "transaction_desc": arguments.get("transaction_desc"),
            "transaction_type": arguments.get("transaction_type"),
            "country": arguments.get("country"),
            "currency": arguments.get("currency"),
            "provider": "Airtel",
        }

        trace_log = {
            "function": func_name,
            "status": "started",
            "timestamp": datetime.utcnow(),
            "transaction": transaction_context,
            "metadata": {
                "env": os.getenv("PROJECT_ENVIRONMENT", "development")
            }
        }

        insert_result = trace_collection.insert_one(trace_log)
        trace_id = insert_result.inserted_id

        try:
            result = await func(*args, **kwargs)

            status = "error" if isinstance(result, dict) and "error" in result else "success"

            trace_collection.update_one(
                {"_id": trace_id},
                {"$set": {
                    "status": status,
                    "duration": round(time.time() - start_time, 3),
                    "timestamp": datetime.utcnow(),
                    "result": result if isinstance(result, dict) else str(result),
                }}
            )
            return result
        except Exception as e:
            trace_collection.update_one(
                {"_id": trace_id},
                {"$set": {
                    "status": "error",
                    "duration": round(time.time() - start_time, 3),
                    "error": str(e),
                    "timestamp": datetime.utcnow(),
                }}
            )
            raise

    return airtel_wrapper