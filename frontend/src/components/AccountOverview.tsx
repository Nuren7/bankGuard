import type { Account } from "@/types/banking";

interface AccountOverviewProps {
  accounts: Account[];
  isLoading: boolean;
  error: string | null;
}

function formatBalance(balance: number, currency: string): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
  }).format(balance);
}

export default function AccountOverview({
  accounts,
  isLoading,
  error,
}: AccountOverviewProps) {
  return (
    <section aria-labelledby="accounts-heading" className="section-panel">
      <div className="section-heading">
        <h2 id="accounts-heading">Accounts</h2>
        <p>{accounts.length} available</p>
      </div>

      {isLoading ? <p className="muted">Loading accounts…</p> : null}
      {error ? <p className="error-message">{error}</p> : null}
      {!isLoading && !error && accounts.length === 0 ? (
        <p className="empty-state">No accounts are available.</p>
      ) : null}

      {accounts.length > 0 ? (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col">Account</th>
                <th scope="col">Number</th>
                <th scope="col">Balance</th>
              </tr>
            </thead>
            <tbody>
              {accounts.map((account) => (
                <tr key={account.id}>
                  <td>{account.id}</td>
                  <td>{account.account_number}</td>
                  <td>{formatBalance(Number(account.balance), account.currency)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}
