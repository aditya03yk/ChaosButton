import { useState } from "react";
import { useNavigate } from "react-router-dom";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import LoadingState from "../components/common/LoadingState";
import PageHeader from "../components/common/PageHeader";
import ExperimentTable from "../components/experiments/ExperimentTable";
import { useAsync } from "../hooks/useAsync";
import { listExperiments } from "../services/experimentService";
import { listTargets } from "../services/targetService";

const PAGE = 15;
const STATUSES = ["CREATED", "RUNNING", "COMPLETED", "STOPPED", "FAILED"];

export default function History() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [target, setTarget] = useState("");
  const [fault, setFault] = useState("");
  const [status, setStatus] = useState("");
  const [newest, setNewest] = useState(true);
  const [page, setPage] = useState(0);
  const [selected, setSelected] = useState<string[]>([]);
  const targets = useAsync(listTargets);
  const { data, error, loading, reload } = useAsync(
    () => listExperiments({ search, target_id: target, fault_type: fault, status, newest_first: newest, offset: page * PAGE, limit: PAGE }),
    [search, target, fault, status, newest, page]);

  const filter = (setter: (v: string) => void) => (e: { target: { value: string } }) => { setter(e.target.value); setPage(0); };
  const toggle = (id: string) => setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id].slice(-2)));
  const pages = data ? Math.max(1, Math.ceil(data.total / PAGE)) : 1;

  return (
    <>
      <PageHeader title="Experiments" subtitle="History of every run." actions={
        <button className="btn" disabled={selected.length !== 2} onClick={() => navigate(`/compare?a=${selected[0]}&b=${selected[1]}`)}>Compare selected (2)</button>} />
      <section className="card mb-4 grid gap-3 md:grid-cols-5">
        <input aria-label="Search by experiment ID" className="input" placeholder="Search by ID" value={search} onChange={filter(setSearch)} />
        <select aria-label="Target" className="input" value={target} onChange={filter(setTarget)}>
          <option value="">All targets</option>{targets.data?.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}</select>
        <select aria-label="Fault type" className="input" value={fault} onChange={filter(setFault)}>
          <option value="">All faults</option>{["latency", "timeout", "http_500", "http_503"].map((f) => <option key={f}>{f}</option>)}</select>
        <select aria-label="Status" className="input" value={status} onChange={filter(setStatus)}>
          <option value="">All statuses</option>{STATUSES.map((s) => <option key={s}>{s}</option>)}</select>
        <button className="btn" onClick={() => setNewest((v) => !v)}>Sort: {newest ? "newest first" : "oldest first"}</button>
      </section>
      <section className="card">
        {loading && !data ? <LoadingState /> : error ? <ErrorState message={error} onRetry={reload} /> :
          !data?.items.length ? <EmptyState title="No experiments match" /> : (
          <>
            <ExperimentTable items={data.items} selected={selected} onToggle={toggle} />
            <div className="mt-3 flex items-center justify-between text-xs text-ink2">
              <span>{data.total} experiments</span>
              <span className="space-x-2">
                <button className="btn px-2 py-0.5" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>Previous</button>
                <span>{page + 1} / {pages}</span>
                <button className="btn px-2 py-0.5" disabled={page + 1 >= pages} onClick={() => setPage((p) => p + 1)}>Next</button>
              </span>
            </div>
          </>)}
      </section>
    </>
  );
}
