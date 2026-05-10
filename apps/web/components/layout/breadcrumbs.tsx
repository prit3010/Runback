"use client";

import { usePathname } from "next/navigation";

function prettify(segment: string) {
  return segment.replace(/-/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function Breadcrumbs() {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);
  if (segments.length === 0) return <span className="text-sm font-medium">Dashboard</span>;
  return (
    <div className="flex flex-wrap items-center gap-1 text-sm text-muted-foreground">
      <span>Dashboard</span>
      {segments.map((segment) => (
        <span key={segment} className="before:mx-1 before:text-muted-foreground before:content-['/'] last:text-foreground">
          {prettify(segment)}
        </span>
      ))}
    </div>
  );
}
