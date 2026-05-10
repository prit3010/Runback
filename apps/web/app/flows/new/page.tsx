"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createFlow } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export default function NewFlowPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [repoPath, setRepoPath] = useState("");
  const [prompt, setPrompt] = useState("");
  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">New flow</h1>
        <p className="text-sm text-muted-foreground">Register a reusable Runback prompt.</p>
      </div>
      <Card>
        <CardHeader><CardTitle>Flow definition</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2"><Label>Name</Label><Input value={name} onChange={(event) => setName(event.target.value)} /></div>
          <div className="space-y-2"><Label>Repository path</Label><Input value={repoPath} onChange={(event) => setRepoPath(event.target.value)} /></div>
          <div className="space-y-2"><Label>Prompt</Label><Textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} /></div>
          <Button onClick={() => createFlow({ name, repo_path: repoPath, prompt }).then((flow) => flow && router.push(`/flows/${flow.id}`))}>Create flow</Button>
        </CardContent>
      </Card>
    </div>
  );
}
