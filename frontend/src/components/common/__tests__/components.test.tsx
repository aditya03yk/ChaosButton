import { render, screen } from "@testing-library/react";
import { messageFromBody } from "../../../services/api";
import EmptyState from "../EmptyState";
import ErrorState from "../ErrorState";
import MetricCard from "../MetricCard";
import StatusBadge from "../StatusBadge";
import EventTimeline from "../../experiments/EventTimeline";
import ProgressIndicator from "../../experiments/ProgressIndicator";
import { fmtMs, fmtSeconds, parseUtc } from "../../../lib/format";

describe("presentational components", () => {
  it("renders a metric card", () => {
    render(<MetricCard label="Error rate" value="50.0%" />);
    expect(screen.getByText("Error rate")).toBeInTheDocument();
    expect(screen.getByText("50.0%")).toBeInTheDocument();
  });

  it("shows the status and an alert with retry", () => {
    render(<><StatusBadge status="RUNNING" /><ErrorState message="Backend down" onRetry={() => {}} /></>);
    expect(screen.getByText("RUNNING")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("Backend down");
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });

  it("shows empty states for no events and no data", () => {
    render(<><EventTimeline events={[]} /><EmptyState title="No experiments yet" /></>);
    expect(screen.getByText("No events yet")).toBeInTheDocument();
    expect(screen.getByText("No experiments yet")).toBeInTheDocument();
  });

  it("renders timeline events", () => {
    render(<EventTimeline events={[{ timestamp: "2026-01-01T02:10:01", level: "warning", message: "Fault activated" }]} />);
    expect(screen.getByText("Fault activated")).toBeInTheDocument();
  });

  it("marks the current phase in the progress indicator", () => {
    render(<ProgressIndicator status="RUNNING" />);
    expect(screen.getByText("RUNNING")).toHaveClass("text-ink");
  });
});

describe("helpers", () => {
  it("formats unavailable values honestly", () => {
    expect(fmtMs(null)).toBe("n/a");
    expect(fmtSeconds(null)).toBe("unavailable");
  });

  it("parses naive backend timestamps as UTC", () => {
    expect(parseUtc("2026-01-01T00:00:00").toISOString()).toBe("2026-01-01T00:00:00.000Z");
  });

  it("extracts readable API errors", () => {
    expect(messageFromBody({ detail: "Nope" }, "x")).toBe("Nope");
    expect(messageFromBody({ detail: [{ loc: ["body", "route"], msg: "bad" }] }, "x")).toBe("route: bad");
    expect(messageFromBody(null, "fallback")).toBe("fallback");
  });
});
