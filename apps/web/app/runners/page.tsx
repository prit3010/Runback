"use client";

import { useQuery } from "@tanstack/react-query";
import { listRunners } from "@/lib/api";
import { timeAgo } from "@/lib/format";
import { FilterBar } from "@/components/filter-bar";
import { StatusPill } from "@/components/status-pill";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function RunnersPage() {
  const runners = useQuery({ queryKey: ["runners"], queryFn: () => listRunners() });
  return (
    <div className="space-y-4">
      <div><h1 className="text-2xl font-semibold">Runners</h1><p className="text-sm text-muted-foreground">Heartbeat and Claude CLI availability.</p></div>
      <FilterBar placeholder="Search runners" chips={["online", "offline", "busy"]} />
      <Card>
        <CardHeader><CardTitle>Runner status</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Status</TableHead><TableHead>Heartbeat</TableHead><TableHead>Claude</TableHead><TableHead>Version</TableHead></TableRow></TableHeader>
            <TableBody>
              {(runners.data ?? []).map((runner) => (
                <TableRow key={runner.id}>
                  <TableCell>{runner.name}</TableCell>
                  <TableCell><StatusPill status={runner.status} /></TableCell>
                  <TableCell>{timeAgo(runner.last_heartbeat_at)}</TableCell>
                  <TableCell>{runner.claude_code_available ? "available" : "missing"}</TableCell>
                  <TableCell>{runner.version}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
