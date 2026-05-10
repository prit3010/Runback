"use client";

import Link from "next/link";
import { useQueries, useQuery } from "@tanstack/react-query";
import { getRunDag, listRuns } from "@/lib/api";
import { FilterBar } from "@/components/filter-bar";
import { StatusPill } from "@/components/status-pill";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function SideEffectsPage() {
  const runs = useQuery({ queryKey: ["runs"], queryFn: () => listRuns() });
  const dagQueries = useQueries({
    queries: (runs.data ?? []).slice(0, 25).map((run) => ({ queryKey: ["run-dag", run.id], queryFn: () => getRunDag(run.id) })),
  });
  const sideEffects = dagQueries.flatMap((query) => query.data?.side_effects ?? []);
  return (
    <div className="space-y-4">
      <div><h1 className="text-2xl font-semibold">Side effects</h1><p className="text-sm text-muted-foreground">Cross-run ledger of external writes and idempotency keys.</p></div>
      <FilterBar placeholder="Search side effects" chips={["executed", "blocked", "reused", "pending_approval"]} />
      <Card>
        <CardHeader><CardTitle>Ledger</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader><TableRow><TableHead>Run</TableHead><TableHead>Kind</TableHead><TableHead>Key</TableHead><TableHead>Status</TableHead><TableHead>External ref</TableHead></TableRow></TableHeader>
            <TableBody>
              {sideEffects.map((effect) => (
                <TableRow key={`${effect.run_id}-${effect.id}`}>
                  <TableCell><Link href={`/runs/${effect.run_id}`} className="font-mono text-xs text-blue-600 underline">{effect.run_id}</Link></TableCell>
                  <TableCell>{effect.kind}</TableCell>
                  <TableCell className="font-mono text-xs">{effect.idempotency_key}</TableCell>
                  <TableCell><StatusPill status={effect.status} /></TableCell>
                  <TableCell>{effect.external_ref ? <a href={effect.external_ref} className="text-blue-600 underline" target="_blank" rel="noreferrer">{effect.external_ref}</a> : "n/a"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
