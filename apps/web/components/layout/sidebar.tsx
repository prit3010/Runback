"use client";

import Link from "next/link";
import { Home, GitBranch, PlayCircle, Radio, ShieldAlert, Settings, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

const items = [
  { href: "/", label: "Dashboard", icon: Home },
  { href: "/flows", label: "Flows", icon: GitBranch },
  { href: "/runs", label: "Runs", icon: PlayCircle },
  { href: "/runners", label: "Runners", icon: Radio },
  { href: "/side-effects", label: "Side effects", icon: ShieldAlert },
];

export function Sidebar({ collapsed, onToggle }: { collapsed: boolean; onToggle: () => void }) {
  return (
    <aside className={cn("flex min-h-screen flex-col border-r bg-card transition-all", collapsed ? "w-16" : "w-56")}>
      <div className="flex h-14 items-center justify-between border-b px-3">
        {!collapsed && <span className="text-sm font-semibold">Runback</span>}
        <Button type="button" variant="ghost" size="icon" onClick={onToggle} aria-label="Toggle sidebar">
          {collapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
        </Button>
      </div>
      <nav className="flex flex-1 flex-col gap-1 p-2">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <Link key={item.href} href={item.href} className="flex items-center gap-2 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-foreground" aria-label={item.label}>
              <Icon className="h-4 w-4 shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>
      <div className="border-t p-2">
        <Link href="/settings" className="flex items-center gap-2 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-foreground" aria-label="Settings">
          <Settings className="h-4 w-4" />
          {!collapsed && <span>Settings</span>}
        </Link>
      </div>
    </aside>
  );
}
