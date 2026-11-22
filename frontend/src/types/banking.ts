export interface Account {
  id: number;
  account_number: string;
  balance: number;
  currency: string;
  updated_at: string;
}

export interface PaymentRequest {
  account_id: number;
  amount: number;
  recipient: string;
  is_foreign: 0 | 1;
}

export interface PaymentResponse {
  transaction_id: number;
  status: string;
  risk_score: number;
  reason: string;
  new_balance: number;
}

export interface AuditLog {
  id: number;
  transaction_id: number;
  event_type: string;
  details: string;
  created_at: string;
}

export interface SessionTransaction extends PaymentResponse {
  request: PaymentRequest;
  idempotency_key: string;
  occurred_at: string;
}

export interface ClearingWebhookPayload {
  event: string;
  transaction_id?: number;
}

export interface ClearingWebhookResponse {
  status: string;
  event: string;
}
