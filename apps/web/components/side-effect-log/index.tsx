import type { components } from "@/lib/api-types";
import { StatusPill } from "@/components/status-pill";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export function SideEffectLog({ sideEffects }: { sideEffects: components["schemas"]["SideEffectLog"][] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Kind</TableHead>
          <TableHead>Idempotency key</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>External ref</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sideEffects.map((effect) => (
          <TableRow key={`${effect.run_id}-${effect.id}`}>
            <TableCell>{effect.kind}</TableCell>
            <TableCell className="font-mono text-xs">{effect.idempotency_key}</TableCell>
            <TableCell>
              <StatusPill status={effect.status} />
            </TableCell>
            <TableCell>
              {effect.external_ref ? (
                <a href={effect.external_ref} className="text-blue-600 underline" target="_blank" rel="noreferrer">
                  {effect.external_ref}
                </a>
              ) : (
                "n/a"
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
