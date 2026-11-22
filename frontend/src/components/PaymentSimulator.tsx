"use client";

import { useEffect, useState, type FormEvent } from "react";
import {
  createIdempotencyKey,
  submitPayment,
} from "@/lib/api";
import type {
  Account,
  PaymentRequest,
  PaymentResponse,
  SessionTransaction,
} from "@/types/banking";

interface PaymentSimulatorProps {
  accounts: Account[];
  onPaymentRecorded: (transaction: SessionTransaction) => void;
}

interface PaymentForm {
  accountId: string;
  amount: string;
  recipient: string;
  isForeign: boolean;
}

function toRequest(form: PaymentForm): PaymentRequest | null {
  const amount = Number(form.amount);
  const accountId = Number(form.accountId);

  if (!Number.isInteger(accountId) || !Number.isFinite(amount) || amount <= 0) {
    return null;
  }

  return {
    account_id: accountId,
    amount,
    recipient: form.recipient.trim(),
    is_foreign: form.isForeign ? 1 : 0,
  };
}

function formatMoney(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "SEK",
  }).format(value);
}

function statusClass(status: string): string {
  if (status === "APPROVED") return "status-label status-approved";
  if (status === "BLOCKED") return "status-label status-blocked";
  return "status-label status-step-up";
}

export default function PaymentSimulator({
  accounts,
  onPaymentRecorded,
}: PaymentSimulatorProps) {
  const [form, setForm] = useState<PaymentForm>({
    accountId: "",
    amount: "250",
    recipient: "Example recipient",
    isForeign: false,
  });
  const [idempotencyKey, setIdempotencyKey] = useState("");
  const [result, setResult] = useState<PaymentResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (form.accountId || accounts.length === 0) return;
    setForm((current) => ({ ...current, accountId: String(accounts[0].id) }));
  }, [accounts, form.accountId]);

  async function runPayment(
    payment: PaymentRequest,
    repeatWithSameKey = false,
  ): Promise<void> {
    if (!payment.recipient) {
      setError("Enter a recipient before submitting the payment.");
      return;
    }

    const key = idempotencyKey.trim() || createIdempotencyKey();
    setIdempotencyKey(key);
    setError(null);
    setResult(null);
    setIsSubmitting(true);

    try {
      const firstResponse = await submitPayment(payment, key);
      setResult(firstResponse);
      onPaymentRecorded(toSessionTransaction(firstResponse, payment, key));

      if (repeatWithSameKey) {
        const secondResponse = await submitPayment(payment, key);
        setResult(secondResponse);
        onPaymentRecorded(toSessionTransaction(secondResponse, payment, key));
      }
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "The payment could not be completed.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  function toSessionTransaction(
    response: PaymentResponse,
    payment: PaymentRequest,
    key: string,
  ): SessionTransaction {
    return {
      ...response,
      request: payment,
      idempotency_key: key,
      occurred_at: new Date().toISOString(),
    };
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const payment = toRequest(form);
    if (!payment) {
      setError("Choose an account and enter a valid amount greater than zero.");
      return;
    }
    void runPayment(payment);
  }

  function runScenario(payment: PaymentRequest, repeatWithSameKey = false) {
    setForm({
      accountId: String(payment.account_id),
      amount: String(payment.amount),
      recipient: payment.recipient,
      isForeign: payment.is_foreign === 1,
    });
    void runPayment(payment, repeatWithSameKey);
  }

  function accountIdForScenario(): number | null {
    const accountId = Number(form.accountId || accounts[0]?.id);
    return Number.isInteger(accountId) && accountId > 0 ? accountId : null;
  }

  function scenarioPayment(amount: number, isForeign: 0 | 1): PaymentRequest | null {
    const accountId = accountIdForScenario();
    if (!accountId) return null;
    return {
      account_id: accountId,
      amount,
      recipient: "Example recipient",
      is_foreign: isForeign,
    };
  }

  const resultStatusClass = result ? statusClass(result.status) : "";

  return (
    <section aria-labelledby="payment-heading" className="section-panel">
      <div className="section-heading">
        <div>
          <h2 id="payment-heading">Payment simulator</h2>
          <p>Submit a payment and review the backend decision.</p>
        </div>
      </div>

      <div className="scenario-row" aria-label="Test scenarios">
        <button
          disabled={isSubmitting || accounts.length === 0}
          onClick={() => {
            const payment = scenarioPayment(250, 0);
            if (payment) runScenario(payment);
          }}
          type="button"
        >
          Run normal payment
        </button>
        <button
          disabled={isSubmitting || accounts.length === 0}
          onClick={() => {
            const payment = scenarioPayment(25_000, 1);
            if (payment) runScenario(payment);
          }}
          type="button"
        >
          Run high-risk payment
        </button>
        <button
          disabled={isSubmitting || accounts.length === 0}
          onClick={() => {
            const payment = scenarioPayment(250, 0);
            if (payment) runScenario(payment, true);
          }}
          type="button"
        >
          Repeat the same key twice
        </button>
      </div>

      <form className="payment-form" onSubmit={handleSubmit}>
        <label>
          <span className="field-label">Account</span>
          <select
            onChange={(event) =>
              setForm((current) => ({ ...current, accountId: event.target.value }))
            }
            required
            value={form.accountId}
          >
            <option value="">Select an account</option>
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.account_number} ({account.currency})
              </option>
            ))}
          </select>
        </label>

        <label>
          <span className="field-label">Amount (SEK)</span>
          <input
            min="0.01"
            onChange={(event) =>
              setForm((current) => ({ ...current, amount: event.target.value }))
            }
            required
            step="0.01"
            type="number"
            value={form.amount}
          />
        </label>

        <label className="recipient-field">
          <span className="field-label">Recipient</span>
          <input
            maxLength={128}
            onChange={(event) =>
              setForm((current) => ({ ...current, recipient: event.target.value }))
            }
            required
            value={form.recipient}
          />
        </label>

        <label className="checkbox-field">
          <input
            checked={form.isForeign}
            onChange={(event) =>
              setForm((current) => ({ ...current, isForeign: event.target.checked }))
            }
            type="checkbox"
          />
          <span>Foreign payment</span>
        </label>

        <div className="key-field">
          <label htmlFor="idempotency-key">
            <span className="field-label">Idempotency key</span>
          </label>
          <div className="key-input-row">
            <input
              autoComplete="off"
              id="idempotency-key"
              onChange={(event) => setIdempotencyKey(event.target.value)}
              placeholder="Generated when you submit"
              value={idempotencyKey}
            />
            <button
              onClick={() => setIdempotencyKey(createIdempotencyKey())}
              type="button"
            >
              New key
            </button>
          </div>
          <p className="field-hint">
            Reuse a key to safely retry the same payment. Generate a new key for a
            different payment.
          </p>
        </div>

        <button
          className="primary-button submit-button"
          disabled={isSubmitting || accounts.length === 0}
          type="submit"
        >
          {isSubmitting ? "Submitting…" : "Submit payment"}
        </button>
      </form>

      {error ? <p className="error-message" role="alert">{error}</p> : null}

      {result ? (
        <section aria-labelledby="result-heading" className="payment-result">
          <div className="section-heading">
            <h3 id="result-heading">Latest result</h3>
            <span className={resultStatusClass}>{result.status.replaceAll("_", " ")}</span>
          </div>
          <dl className="result-grid">
            <div>
              <dt>Transaction</dt>
              <dd>{result.transaction_id}</dd>
            </div>
            <div>
              <dt>Risk score</dt>
              <dd>{result.risk_score} / 100</dd>
            </div>
            <div>
              <dt>Balance after</dt>
              <dd>{formatMoney(result.new_balance)}</dd>
            </div>
            <div className="result-reason">
              <dt>Reason</dt>
              <dd>{result.reason}</dd>
            </div>
          </dl>
        </section>
      ) : null}
    </section>
  );
}
