"use client";

import { TabsList, TabsTrigger } from "@/components/ui/tabs";

export function TabsHeader({ tabs }: { tabs: { value: string; label: string }[] }) {
  return (
    <TabsList className="flex h-auto flex-wrap justify-start">
      {tabs.map((tab) => (
        <TabsTrigger key={tab.value} value={tab.value}>
          {tab.label}
        </TabsTrigger>
      ))}
    </TabsList>
  );
}
