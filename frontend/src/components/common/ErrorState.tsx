export default function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="rounded-md border border-bad/50 bg-bad/10 px-4 py-3 text-sm">
      <div className="text-bad">{message}</div>
      {onRetry && <button className="btn mt-2" onClick={onRetry}>Retry</button>}
    </div>
  );
}
