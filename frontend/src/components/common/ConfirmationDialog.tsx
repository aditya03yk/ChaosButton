interface Props { open: boolean; title: string; message: string; confirmLabel?: string; onConfirm: () => void; onCancel: () => void }

export default function ConfirmationDialog({ open, title, message, confirmLabel = "Confirm", onConfirm, onCancel }: Props) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" role="dialog" aria-modal="true">
      <div className="card w-full max-w-sm">
        <h2>{title}</h2>
        <p className="mt-2 text-sm text-ink2">{message}</p>
        <div className="mt-4 flex justify-end gap-2">
          <button className="btn" onClick={onCancel}>Cancel</button>
          <button className="btn btn-danger" onClick={onConfirm}>{confirmLabel}</button>
        </div>
      </div>
    </div>
  );
}
