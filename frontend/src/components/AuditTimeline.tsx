import type { AuditLog } from "@/types/banking";

interface AuditTimelineProps {
  entries: AuditLog[];
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default function AuditTimeline({ entries }: AuditTimelineProps) {
  const chronologicalEntries = [...entries].sort((first, second) => {
    const dateOrder =
      new Date(first.created_at).getTime() - new Date(second.created_at).getTime();
    return dateOrder || first.id - second.id;
  });

  if (chronologicalEntries.length === 0) {
    return <p className="empty-state">No audit entries are available.</p>;
  }

  return (
    <ol className="audit-list">
      {chronologicalEntries.map((entry) => (
        <li className="audit-entry" key={entry.id}>
          <div className="audit-entry-heading">
            <strong>{entry.event_type.replaceAll("_", " ")}</strong>
            <time dateTime={entry.created_at}>{formatDate(entry.created_at)}</time>
          </div>
          <p className="audit-transaction">Transaction {entry.transaction_id}</p>
          <p className="audit-details">{entry.details}</p>
        </li>
      ))}
    </ol>
  );
}
