export default function LoadingState({ label = "Loading…" }: { label?: string }) {
  return <div role="status" className="animate-pulse py-8 text-center text-xs text-ink2">{label}</div>;
}
