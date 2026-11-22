"use client";

import { useCallback, useEffect, useState } from "react";
import AccountOverview from "@/components/AccountOverview";
import PaymentSimulator from "@/components/PaymentSimulator";
import TransactionFeed from "@/components/TransactionFeed";
import { getAccounts } from "@/lib/api";
import type { Account, SessionTransaction } from "@/types/banking";

export default function HomePage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [accountError, setAccountError] = useState<string | null>(null);
  const [isLoadingAccounts, setIsLoadingAccounts] = useState(true);
  const [transactions, setTransactions] = useState<SessionTransaction[]>([]);

  const loadAccounts = useCallback(async (signal?: AbortSignal) => {
    setIsLoadingAccounts(true);
    setAccountError(null);

    try {
      setAccounts(await getAccounts(signal));
    } catch (error) {
      if (signal?.aborted) return;
      setAccountError(
        error instanceof Error ? error.message : "Accounts could not be loaded.",
      );
    } finally {
      if (!signal?.aborted) setIsLoadingAccounts(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void loadAccounts(controller.signal);
    return () => controller.abort();
  }, [loadAccounts]);

  function recordTransaction(transaction: SessionTransaction) {
    setTransactions((current) => {
      const existingIndex = current.findIndex(
        (item) => item.transaction_id === transaction.transaction_id,
      );
      if (existingIndex < 0) return [transaction, ...current];

      return current.map((item, index) =>
        index === existingIndex ? transaction : item,
      );
    });
    void loadAccounts();
  }

  return (
    <main className="page-shell">
      <div className="page-heading">
        <h1>Payments</h1>
        <p>Review accounts, submit a payment, and inspect its risk assessment.</p>
      </div>

      <div className="dashboard-grid">
        <AccountOverview
          accounts={accounts}
          error={accountError}
          isLoading={isLoadingAccounts}
        />
        <PaymentSimulator
          accounts={accounts}
          onPaymentRecorded={recordTransaction}
        />
      </div>

      <div className="feed-section">
        <TransactionFeed transactions={transactions} />
      </div>
    </main>
  );
}
