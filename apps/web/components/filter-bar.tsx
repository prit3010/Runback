"use client";

import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export function FilterBar({
  placeholder = "Search",
  chips = [],
}: {
  placeholder?: string;
  chips?: string[];
}) {
  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div className="relative max-w-md flex-1">
        <Search className="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input className="pl-8" placeholder={placeholder} aria-label={placeholder} />
      </div>
      <div className="flex flex-wrap gap-2">
        {["all", ...chips].map((chip) => (
          <Button key={chip} type="button" variant={chip === "all" ? "secondary" : "outline"} size="sm">
            {chip}
          </Button>
        ))}
      </div>
    </div>
  );
}
