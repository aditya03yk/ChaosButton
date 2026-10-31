import { useState } from "react";
import { useNavigate } from "react-router-dom";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import LoadingState from "../components/common/LoadingState";
import PageHeader from "../components/common/PageHeader";
import ExperimentForm from "../components/experiments/ExperimentForm";
import { useAsync } from "../hooks/useAsync";
import { createExperiment, startExperiment } from "../services/experimentService";
import { getConfig } from "../services/reportService";
import { listTargets } from "../services/targetService";
import type { ExperimentInput } from "../types/experiment";

export default function ManualChaosTest() {
  const navigate = useNavigate();
  const targets = useAsync(listTargets);
  const config = useAsync(getConfig);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (input: ExperimentInput) => {
    setBusy(true);
    try {
      const created = await createExperiment(input);
      await startExperiment(created.id);
      navigate(`/experiments/${created.id}/live`);
    } catch (e) { setError((e as Error).message); setBusy(false); }
  };

  if (targets.loading || config.loading) return <LoadingState />;
  if (targets.error || config.error) return <ErrorState message={(targets.error ?? config.error)!} onRetry={targets.reload} />;
  return (
    <>
      <PageHeader title="Manual Chaos Test" subtitle="Precise control over one fault, route and limit." />
      {!targets.data?.length ? <EmptyState title="No targets yet" text="Register a target on the Targets page first." /> : (
        <section className="card max-w-3xl">
          {error && <div role="alert" className="mb-3 text-xs text-bad">{error}</div>}
          <ExperimentForm targets={targets.data} limits={config.data?.limits ?? {}} submitting={busy} onSubmit={submit} />
        </section>
      )}
    </>
  );
}
