import { Activity, BarChart3, Bot, FlaskConical, LayoutDashboard, Settings, SlidersHorizontal, Target } from "lucide-react";
import { NavLink } from "react-router-dom";

const ITEMS = [
  { to: "/", label: "Overview", icon: LayoutDashboard },
  { to: "/targets", label: "Targets", icon: Target },
  { to: "/auto", label: "Auto Chaos Test", icon: FlaskConical },
  { to: "/manual", label: "Manual Test", icon: SlidersHorizontal },
  { to: "/experiments", label: "Experiments", icon: Activity },
  { to: "/compare", label: "Reports", icon: BarChart3 },
  { to: "/analysis", label: "AI Assistant", icon: Bot },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar({ onNavigate }: { onNavigate: () => void }) {
  return (
    <nav className="flex h-full w-60 flex-col border-r border-line bg-sidebar" aria-label="Main">
      <div className="px-4 py-4">
        <div className="font-semibold tracking-tight">Chaos<span className="text-accent">Button</span></div>
        <div className="text-xs text-muted">Break it before your users do.</div>
      </div>
      <ul className="flex-1 space-y-0.5 px-2">
        {ITEMS.map(({ to, label, icon: Icon }) => (
          <li key={to}>
            <NavLink to={to} end={to === "/"} onClick={onNavigate}
              className={({ isActive }) => `flex items-center gap-2 rounded px-2.5 py-1.5 text-sm transition-colors ${
                isActive ? "bg-surface2 text-ink" : "text-ink2 hover:bg-surface hover:text-ink"}`}>
              <Icon size={15} /> {label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
