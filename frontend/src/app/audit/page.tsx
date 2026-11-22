"use client";

import { useEffect, useMemo, useState, type FormEvent } from "react";
import AuditTimeline from "@/components/AuditTimeline";
import { getAuditLogs, sendClearingWebhook } from "@/lib/api";
import type {
  AuditLog,
  ClearingWebhookPayload,
  ClearingWebhookResponse,
} from "@/types/banking";

export default function AuditPage() {
  const [entries, setEntries] = useState<AuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [event, setEvent] = useState("CLEARING_CONFIRMED");
  const [transactionId, setTransactionId] = useState("");
  const [signature, setSignature] = useState("");
  const [webhookError, setWebhookError] = useState<string | null>(null);
  const [webhookResult, setWebhookResult] =
    useState<ClearingWebhookResponse | null>(null);
  const [isSending, setIsSending] = useState(false);

  const payload = useMemo<ClearingWebhookPayload>(() => {
    const parsedTransactionId = Number(transactionId);
    return {
      event: event.trim(),
      ...(transactionId.trim() &&
      Number.isInteger(parsedTransactionId) &&
      parsedTransactionId > 0
        ? { transaction_id: parsedTransactionId }
        : {}),
    };
  }, [event, transactionId]);

  useEffect(() => {
    const controller = new AbortController();

    async function loadEntries() {
      setIsLoading(true);
      setLoadError(null);
      try {
        setEntries(await getAuditLogs(controller.signal));
      } catch (error) {
        if (!controller.signal.aborted) {
          setLoadError(
            error instanceof Error ? error.message : "Audit logs could not be loaded.",
          );
        }
      } finally {
        if (!controller.signal.aborted) setIsLoading(false);
      }
    }

    void loadEntries();
    return () => controller.abort();
  }, []);

  async function handleWebhookSubmit(eventObject: FormEvent<HTMLFormElement>) {
    eventObject.preventDefault();
    setWebhookError(null);
    setWebhookResult(null);

    if (!payload.event) {
      setWebhookError("Enter an event name.");
      return;
    }

    if (transactionId.trim() && !payload.transaction_id) {
      setWebhookError("Transaction ID must be a positive whole number.");
      return;
    }

    setIsSending(true);
    try {
      const result = await sendClearingWebhook(payload, signature.trim());
      setWebhookResult(result);
      try {
        setEntries(await getAuditLogs());
      } catch (error) {
        setLoadError(
          error instanceof Error ? error.message : "Audit logs could not be refreshed.",
        );
      }
    } catch (error) {
      setWebhookError(
        error instanceof Error ? error.message : "The clearing event could not be sent.",
      );
    } finally {
      setIsSending(false);
    }
  }

  return (
    <main className="page-shell">
      <div className="page-heading">
        <h1>Audit logs</h1>
        <p>Review transaction audit events in chronological order.</p>
      </div>

      <section aria-labelledby="audit-heading" className="section-panel">
        <div className="section-heading">
          <h2 id="audit-heading">Audit timeline</h2>
          <p>{entries.length} entries</p>
        </div>
        {isLoading ? <p className="muted">Loading audit logs…</p> : null}
        {loadError ? <p className="error-message" role="alert">{loadError}</p> : null}
        {!isLoading && !loadError ? <AuditTimeline entries={entries} /> : null}
      </section>

      <section aria-labelledby="clearing-heading" className="section-panel clearing-panel">
        <div className="section-heading">
          <div>
            <h2 id="clearing-heading">Send a clearing event</h2>
            <p>Submit a signed event to the clearing webhook.</p>
          </div>
        </div>
        <form className="clearing-form" onSubmit={handleWebhookSubmit}>
          <label>
            <span className="field-label">Event name</span>
            <input
              onChange={(change) => setEvent(change.target.value)}
              required
              value={event}
            />
          </label>
          <label>
            <span className="field-label">Transaction ID (optional)</span>
            <input
              min="1"
              onChange={(change) => setTransactionId(change.target.value)}
              type="number"
              value={transactionId}
            />
          </label>
          <label className="signature-field">
            <span className="field-label">HMAC signature</span>
            <input
              autoComplete="off"
              onChange={(change) => setSignature(change.target.value)}
              placeholder="sha256=<hex>"
              required
              value={signature}
            />
          </label>
          <div className="payload-preview">
            <span className="field-label">Signed payload</span>
            <code>{JSON.stringify(payload)}</code>
          </div>
          <button className="primary-button" disabled={isSending} type="submit">
            {isSending ? "Sending…" : "Send clearing event"}
          </button>
        </form>
        <p className="field-hint">
          The signature must match the exact payload shown above. The HMAC secret is
          never stored in or sent from this browser.
        </p>
        {webhookError ? (
          <p className="error-message" role="alert">{webhookError}</p>
        ) : null}
        {webhookResult ? (
          <p className="success-message" role="status">
            Webhook accepted: {webhookResult.event} ({webhookResult.status}).
          </p>
        ) : null}
      </section>
    </main>
  );
}
