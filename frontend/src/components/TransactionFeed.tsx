"use client";

import { useState } from "react";
import type { SessionTransaction } from "@/types/banking";
import AiInspectionModal from "@/components/AiInspectionModal";

interface TransactionFeedProps {
  transactions: SessionTransaction[];
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
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

export default function TransactionFeed({ transactions }: TransactionFeedProps) {
  const [selected, setSelected] = useState<SessionTransaction | null>(null);
  const sortedTransactions = [...transactions].sort(
    (first, second) =>
      new Date(second.occurred_at).getTime() - new Date(first.occurred_at).getTime(),
  );

  return (
    <section aria-labelledby="transactions-heading" className="section-panel">
      <div className="section-heading">
        <div>
          <h2 id="transactions-heading">Session transactions</h2>
          <p>Payments submitted during this session.</p>
        </div>
        <span className="muted">{transactions.length}</span>
      </div>

      {transactions.length === 0 ? (
        <p className="empty-state">Submitted payments will appear here.</p>
      ) : (
        <div className="table-wrap">
          <table className="data-table transaction-table">
            <thead>
              <tr>
                <th scope="col">Time</th>
                <th scope="col">Recipient</th>
                <th scope="col">Amount</th>
                <th scope="col">Decision</th>
                <th scope="col">Risk</th>
                <th scope="col">
                  <span className="visually-hidden">Details</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedTransactions.map((transaction) => (
                <tr key={transaction.transaction_id}>
                  <td>{formatDate(transaction.occurred_at)}</td>
                  <td>{transaction.request.recipient}</td>
                  <td>{formatMoney(transaction.request.amount)}</td>
                  <td>
                    <span className={statusClass(transaction.status)}>
                      {transaction.status.replaceAll("_", " ")}
                    </span>
                  </td>
                  <td>{transaction.risk_score}</td>
                  <td>
                    <button
                      className="text-button"
                      onClick={() => setSelected(transaction)}
                      type="button"
                    >
                      Inspect
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {selected ? (
        <AiInspectionModal
          onClose={() => setSelected(null)}
          transaction={selected}
        />
      ) : null}
    </section>
  );
}
