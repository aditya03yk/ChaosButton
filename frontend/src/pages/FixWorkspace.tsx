import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import FixPanel from "../components/ai/FixPanel";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import LoadingState from "../components/common/LoadingState";
import PageHeader from "../components/common/PageHeader";
import TargetSelector from "../components/experiments/TargetSelector";
import { useAsync } from "../hooks/useAsync";
import { getExperiment, listFixes, retest, startExperiment } from "../services/experimentService";
import { listTargets } from "../services/targetService";

export default function FixWorkspace() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const fixes = useAsync(() => listFixes(id), [id]);
  const exp = useAsync(() => getExperiment(id), [id]);
  const targets = useAsync(listTargets);
  const [retestTarget, setRetestTarget] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const rerun = async () => {
    try {
      const next = await retest(id, retestTarget ?? undefined);
      await startExperiment(next.id);
      navigate(`/experiments/${next.id}/live`);
    } catch (e) { setError((e as Error).message); }
  };

  if (fixes.loading && !fixes.data) return <LoadingState />;
  if (fixes.error) return <ErrorState message={fixes.error} onRetry={fixes.reload} />;

  return (
    <>
      <PageHeader title="Fix workspace" subtitle={`Proposals for ${id}. You apply changes yourself; ChaosButton never edits your code.`} />
      <section className="card mb-4 max-w-xl space-y-2">
        <h2>Verify with a retest</h2>
        {targets.data && <TargetSelector targets={targets.data} value={retestTarget} onChange={setRetestTarget} label="Retest on (leave empty for the same target)" />}
        {error && <div role="alert" className="text-xs text-bad">{error}</div>}
        <button className="btn" onClick={rerun}>Rerun the original experiment</button>
      </section>
      {!fixes.data?.length ? <EmptyState title="No fix proposals" text="Run an AI analysis for this experiment to generate one." /> : (
        <div className="space-y-4">
          {fixes.data.map((item) => (
            <FixPanel key={item.fix.id} item={item} route={exp.data?.route ?? ""} onChanged={fixes.reload} onRetest={rerun} />
          ))}
        </div>
      )}
    </>
  );
}
