import { useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

export default function AppLayout() {
  const [open, setOpen] = useState(false);
  return (
    <div className="flex h-screen">
      <div className={`fixed inset-y-0 left-0 z-40 lg:static ${open ? "block" : "hidden"} lg:block`}>
        <Sidebar onNavigate={() => setOpen(false)} />
      </div>
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar onMenu={() => setOpen((v) => !v)} />
        <main className="flex-1 overflow-y-auto p-5"><div className="mx-auto max-w-6xl"><Outlet /></div></main>
      </div>
    </div>
  );
}
