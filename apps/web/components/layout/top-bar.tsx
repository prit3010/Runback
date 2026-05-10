"use client";

import { Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { ThemeToggle } from "@/components/theme-toggle";

export function TopBar({ onOpenCommand }: { onOpenCommand: () => void }) {
  return (
    <header className="flex h-14 items-center justify-between border-b bg-background px-4">
      <Breadcrumbs />
      <div className="flex items-center gap-2">
        <Button type="button" variant="outline" size="sm" className="hidden min-w-48 justify-start text-muted-foreground sm:inline-flex" onClick={onOpenCommand}>
          <Search className="h-4 w-4" />
          Command
          <kbd className="ml-auto text-xs">⌘K</kbd>
        </Button>
        <ThemeToggle />
      </div>
    </header>
  );
}
