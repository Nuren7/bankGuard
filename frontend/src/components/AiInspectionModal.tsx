"use client";

import { useEffect } from "react";
import type { SessionTransaction } from "@/types/banking";

interface AiInspectionModalProps {
  transaction: SessionTransaction;
  onClose: () => void;
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default function AiInspectionModal({
  transaction,
  onClose,
}: AiInspectionModalProps) {
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div
      className="modal-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <section
        aria-labelledby="inspection-title"
        aria-modal="true"
        className="inspection-modal"
        role="dialog"
      >
        <div className="section-heading">
          <div>
            <p className="eyebrow">Transaction {transaction.transaction_id}</p>
            <h2 id="inspection-title">Risk assessment</h2>
          </div>
          <button aria-label="Close risk assessment" onClick={onClose} type="button">
            Close
          </button>
        </div>
        <dl className="inspection-details">
          <div>
            <dt>Decision</dt>
            <dd>{transaction.status.replaceAll("_", " ")}</dd>
          </div>
          <div>
            <dt>Risk score</dt>
            <dd>{transaction.risk_score} / 100</dd>
          </div>
          <div>
            <dt>Recipient</dt>
            <dd>{transaction.request.recipient}</dd>
          </div>
          <div>
            <dt>Amount</dt>
            <dd>
              {new Intl.NumberFormat("en-US", {
                style: "currency",
                currency: "SEK",
              }).format(transaction.request.amount)}
            </dd>
          </div>
          <div>
            <dt>Reviewed</dt>
            <dd>{formatDate(transaction.occurred_at)}</dd>
          </div>
          <div className="inspection-reason">
            <dt>Reason</dt>
            <dd>{transaction.reason}</dd>
          </div>
        </dl>
      </section>
    </div>
  );
}
