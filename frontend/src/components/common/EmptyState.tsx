import type { ReactNode } from "react";

export default function EmptyState({ title, text, action }: { title: string; text?: string; action?: ReactNode }) {
  return (
    <div className="rounded-md border border-dashed border-line px-4 py-8 text-center">
      <div className="font-medium">{title}</div>
      {text && <p className="mt-1 text-xs text-ink2">{text}</p>}
      {action && <div className="mt-3">{action}</div>}
    </div>
  );
}
