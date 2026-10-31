import { Route, Routes } from "react-router-dom";
import AppLayout from "./components/layout/AppLayout";
import AIAnalysis from "./pages/AIAnalysis";
import AutoChaosTest from "./pages/AutoChaosTest";
import CompareRuns from "./pages/CompareRuns";
import Dashboard from "./pages/Dashboard";
import FixWorkspace from "./pages/FixWorkspace";
import History from "./pages/History";
import LiveExperiment from "./pages/LiveExperiment";
import ManualChaosTest from "./pages/ManualChaosTest";
import Report from "./pages/Report";
import Results from "./pages/Results";
import Settings from "./pages/Settings";
import Targets from "./pages/Targets";

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="targets" element={<Targets />} />
        <Route path="auto" element={<AutoChaosTest />} />
        <Route path="auto/:suiteId" element={<AutoChaosTest />} />
        <Route path="manual" element={<ManualChaosTest />} />
        <Route path="experiments" element={<History />} />
        <Route path="experiments/:id/live" element={<LiveExperiment />} />
        <Route path="experiments/:id/results" element={<Results />} />
        <Route path="experiments/:id/report" element={<Report />} />
        <Route path="experiments/:id/analysis" element={<AIAnalysis />} />
        <Route path="experiments/:id/fixes" element={<FixWorkspace />} />
        <Route path="analysis" element={<AIAnalysis />} />
        <Route path="compare" element={<CompareRuns />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}
