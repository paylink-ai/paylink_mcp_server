import os
import json
from typing import Dict, Any
from mcp.server.fastmcp import Context
from src.servers.mpesa.models.context import MPesaContext
from src.servers.mpesa.core.mpesa_express.stk_push import initiate_stk_push
from src.servers.mpesa.core.mpesa_express.query_stk_push_status import query_stk_push_status
from src.servers.mpesa.core.mpesa_qr.generate_dynamic_qr import generate_dynamic_qr
from src.servers.mpesa.core.c2b.initiate_c2b_payment import initiate_c2b_payment
from src.servers.mpesa.core.b2c.disburse_funds import disburse_funds
from src.servers.mpesa.utils.auth import get_access_token
from starlette.requests import Request


class MpesaTools:
    def __init__(self, mcp) -> None:
        """
        Initializes the MpesaTools class and registers available tools.
        """
        self.mcp = mcp
        self.register_tools()


    def register_tools(self):
        """
        Registers available tools
        """
        @self.mcp.tool()
        async def stk_push(
            ctx: Context,
            phone_number: str,
            amount: int,
            account_reference: str,
            transaction_desc: str,
            transaction_type: str,
        ) -> Dict[str, Any]:
            """
            Initiates an M-Pesa STK Push transaction to request payment from a customer.
            
            This tool triggers the M-Pesa Lipa na M-Pesa Online API (STK Push), which sends a payment
            request to the customer's M-Pesa registered phone number. The customer receives a prompt
            on their phone to enter their M-Pesa PIN to authorize and complete the payment.
            
            Args:
                phone_number: The mobile number to receive the STK push (format: 254XXXXXXXXX)
                amount: The amount to be paid (integer value)
                account_reference: Reference for the transaction (max 12 characters)
                transaction_desc: Description of the transaction (max 13 characters)
                transaction_type: Type of transaction, must be one of:
                    - "CustomerPayBillOnline" - For pay bill transactions
                    - "CustomerBuyGoodsOnline" - For buy goods transactions
            
            Returns:
                JSON response from the M-Pesa API or error message
            """
            try:
                mpesa_ctx = await get_access_token(ctx)

                response = await initiate_stk_push(
                    mpesa_ctx.access_token,
                    phone_number,
                    amount,
                    account_reference,
                    transaction_desc,
                    transaction_type,
                    headers=mpesa_ctx.headers,
                )
                return json.dumps(response, indent=2)
            except Exception as e:
                return {"error": f"Failed to initiate STK push: {str(e)}"}

        @self.mcp.tool()
        async def stk_push_status(
            ctx: Context,
            checkout_request_id: str,
        ) -> Dict[str, Any]:
            """
            Queries the status of a previously initiated M-Pesa STK Push transaction.
            
            This tool checks whether a payment request was successful, is pending, or failed.
            It uses the CheckoutRequestID that was returned when the STK push was initiated.
            
            Args:
                checkout_request_id: The unique identifier received from a previous stk_push call
            
            Returns:
                JSON response containing the transaction status or error message
            """
            try:
                mpesa_ctx = await get_access_token(ctx)

                response = await query_stk_push_status(
                    mpesa_ctx.access_token,
                    checkout_request_id,
                    headers=mpesa_ctx.headers
                )
                return json.dumps(response, indent=2)
            except Exception as e:
                return {"error": f"Failed to query STK push status: {str(e)}"}

        @self.mcp.tool()
        async def generate_qr_code(
            ctx: Context,
            merchant_name: str,
            ref_no: str,
            amount: int,
            trx_code: str,
            cpi: str,
            size: str = "300",
        ) -> Dict[str, Any]:
            """
            Generate a dynamic QR code for M-Pesa payments.
            
            Args:
                merchant_name: Name of the merchant
                ref_no: Reference number for the transaction
                amount: Amount for the transaction (integer)
                trx_code: Transaction code (BG, WA, PB, SM, or SB)
                    BG - Buy Goods
                    WA - Withdraw Cash at Agent Till
                    PB - Pay Bill
                    SM - Send Money
                    SB - Send Business Money
                cpi: Customer Identifier (phone number for SM/SB, account number for PB)
                size: QR code size in pixels (default: 300)
                
            Returns:
                QR code data or error message
            """
            try:
                # Validate transaction code
                valid_trx_codes = ["BG", "WA", "PB", "SM", "SB"]
                if trx_code not in valid_trx_codes:
                    return {
                        "error": f"Invalid transaction code: {trx_code}. Must be one of: {', '.join(valid_trx_codes)}"
                    }
                
                mpesa_ctx = await get_access_token(ctx)

                payload = {
                    "MerchantName": merchant_name,
                    "RefNo": ref_no,
                    "Amount": amount,
                    "TrxCode": trx_code,
                    "CPI": cpi,
                    "Size": size,
                }

                response = await generate_dynamic_qr(mpesa_ctx.access_token, payload, headers=mpesa_ctx.headers)
                return response
            except Exception as e:
                return {"error": f"Failed to generate QR code: {str(e)}"}
