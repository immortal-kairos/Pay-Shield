import razorpay
import asyncio
from decimal import Decimal
from uuid import UUID
from app.core.errors import PayShieldError, ErrorCode

class PaymentRailService:
    def __init__(self, key_id: str, key_secret: str):
        self.client = razorpay.Client(auth=(key_id, key_secret))

    async def initiate_payout(
        self,
        payment_id: UUID,
        vendor_account_number: str,
        vendor_name: str,
        vendor_ifsc: str,
        amount_inr: Decimal,
        reference_note: str | None,
        source_account: str
    ) -> dict:
        amount_paise = int(amount_inr * 100)
        
        data = {
            "account_number": source_account,
            "fund_account": {
                "account_type": "bank_account",
                "bank_account": {
                    "name": vendor_name,
                    "ifsc": vendor_ifsc,
                    "account_number": vendor_account_number
                }
            },
            "amount": amount_paise,
            "currency": "INR",
            "mode": "NEFT",
            "purpose": "vendor_payment",
            "reference_id": str(payment_id),
            "notes": {
                "reference_note": reference_note or ""
            }
        }
        
        try:
            # SDK is synchronous, executing in thread pool to prevent blocking the event loop
            response = await asyncio.to_thread(
                self.client.payout.create, 
                data, 
                {"idempotency_key": str(payment_id)}
            )
            return response
        except razorpay.errors.BadRequestError as e:
            raise PayShieldError(400, ErrorCode.INTERNAL_ERROR, str(e))
        except razorpay.errors.ServerError as e:
            raise PayShieldError(502, ErrorCode.INTERNAL_ERROR, str(e))

    @staticmethod
    def verify_webhook_signature(payload_body: bytes, razorpay_signature: str, webhook_secret: str) -> bool:
        try:
            utility = razorpay.utility.Utility()
            utility.verify_webhook_signature(payload_body.decode('utf-8'), razorpay_signature, webhook_secret)
            return True
        except Exception:
            return False
            