import type {
  Account,
  AuditLog,
  ClearingWebhookPayload,
  ClearingWebhookResponse,
  PaymentRequest,
  PaymentResponse,
} from "@/types/banking";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL?.trim().replace(/\/+$/, "");

function buildApiUrl(path: string): string {
  if (!API_BASE_URL) {
    throw new Error("NEXT_PUBLIC_API_URL must be set to the backend URL.");
  }

  return `${API_BASE_URL}/${path.replace(/^\/+/, "")}`;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  const headers = new Headers(init?.headers);
  if (init?.body !== undefined && init.body !== null && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  try {
    response = await fetch(buildApiUrl(path), {
      ...init,
      headers,
      cache: "no-store",
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "The API request could not be completed.";
    throw new ApiError(message, 0);
  }

  const rawBody = await response.text();
  let body: unknown = null;
  if (rawBody) {
    try {
      body = JSON.parse(rawBody) as unknown;
    } catch {
      body = rawBody;
    }
  }

  if (!response.ok) {
    const detail =
      typeof body === "object" && body !== null && "detail" in body
        ? String(body.detail)
        : typeof body === "string" && body.length > 0
          ? body
          : `The API returned HTTP ${response.status}.`;
    throw new ApiError(detail, response.status);
  }

  return body as T;
}

export function getAccounts(signal?: AbortSignal): Promise<Account[]> {
  return request<Account[]>("/api/accounts", { signal });
}

export function getAuditLogs(signal?: AbortSignal): Promise<AuditLog[]> {
  return request<AuditLog[]>("/api/accounts/audit-logs", { signal });
}

export function createIdempotencyKey(): string {
  if (typeof globalThis.crypto?.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function submitPayment(
  payment: PaymentRequest,
  idempotencyKey: string,
): Promise<PaymentResponse> {
  return request<PaymentResponse>("/api/payments", {
    method: "POST",
    headers: {
      "Idempotency-Key": idempotencyKey,
    },
    body: JSON.stringify(payment),
  });
}

export function sendClearingWebhook(
  payload: ClearingWebhookPayload,
  signature: string,
): Promise<ClearingWebhookResponse> {
  return request<ClearingWebhookResponse>("/api/webhooks/clearing", {
    method: "POST",
    headers: {
      "X-Signature": signature,
    },
    body: JSON.stringify(payload),
  });
}
