import type { ExperimentStatus } from "../../types/experiment";

const STEPS: ExperimentStatus[] = ["VALIDATING", "BASELINE", "RUNNING", "RECOVERING", "COMPLETED"];

export default function ProgressIndicator({ status }: { status: ExperimentStatus }) {
  const index = STEPS.indexOf(status);
  const ended = status === "STOPPED" || status === "FAILED";
  return (
    <ol className="flex items-center gap-1" aria-label="Experiment progress">
      {STEPS.map((step, i) => {
        const done = !ended && i <= index && index >= 0;
        return (
          <li key={step} className="flex flex-1 flex-col gap-1">
            <div className={`h-1 rounded ${done ? (step === status && step !== "COMPLETED" ? "bg-accent" : "bg-ok") : "bg-line"}`} />
            <span className={`text-[10px] uppercase ${step === status ? "text-ink" : "text-muted"}`}>{step}</span>
          </li>
        );
      })}
    </ol>
  );
}
