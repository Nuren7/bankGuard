import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "BankGuard",
  description: "BankGuard payment review and audit console.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <header className="topbar">
          <div className="topbar-inner">
            <Link className="brand" href="/">
              BankGuard
            </Link>
            <nav aria-label="Main navigation" className="navigation">
              <Link href="/">Payments</Link>
              <Link href="/audit">Audit logs</Link>
            </nav>
          </div>
        </header>
        {children}
      </body>
    </html>
  );
}
