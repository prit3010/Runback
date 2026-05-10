"use client";

import { useState } from "react";
import { overrideNodePolicy } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export function OverrideDialog({ runId, nodeId }: { runId: string; nodeId: string }) {
  const [reason, setReason] = useState("");
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">Override policy</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Override recovery policy</DialogTitle>
        </DialogHeader>
        <div className="space-y-2">
          <Label htmlFor="override-reason">Reason</Label>
          <Textarea id="override-reason" value={reason} onChange={(event) => setReason(event.target.value)} />
        </div>
        <DialogFooter>
          <Button onClick={() => overrideNodePolicy(runId, nodeId, { recovery_policy: "requires_approval", reason })}>Require approval</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
