from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

class PaymentRequest(BaseModel):
    account_id: int = Field(..., description="Payment account ID")
    amount: float = Field(..., gt=0, description="Amount must be greater than zero")
    recipient: str = Field(..., min_length=1, max_length=128)
    is_foreign: int = Field(default=0, ge=0, le=1, description="0 = domestic, 1 = foreign")

class PaymentResponse(BaseModel):
    transaction_id: int
    status: str
    risk_score: int
    reason: str
    new_balance: float

    model_config = ConfigDict(from_attributes=True)

class AccountResponse(BaseModel):
    id: int
    account_number: str
    balance: float
    currency: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AuditLogResponse(BaseModel):
    id: int
    transaction_id: int
    event_type: str
    details: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)