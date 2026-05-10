"use client";

import { useCallback, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { TopBar } from "@/components/layout/top-bar";
import { CommandPalette } from "@/components/command-palette";
import { useShortcut } from "@/lib/keyboard";

export function AppShell({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const router = useRouter();
  const toggleSidebar = useCallback(() => setCollapsed((value) => !value), []);
  useShortcut("mod+k", () => setCommandOpen(true));
  useShortcut("mod+b", toggleSidebar);
  useShortcut("g h", () => router.push("/"));
  useShortcut("g f", () => router.push("/flows"));
  useShortcut("g r", () => router.push("/runs"));
  useShortcut("g s", () => router.push("/side-effects"));

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar collapsed={collapsed} onToggle={toggleSidebar} />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar onOpenCommand={() => setCommandOpen(true)} />
        <main className="min-w-0 flex-1 p-4">{children}</main>
      </div>
      <CommandPalette open={commandOpen} onOpenChange={setCommandOpen} />
    </div>
  );
}
