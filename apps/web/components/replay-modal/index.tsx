"use client";

import { useEffect, useState } from "react";
import { getReplayRecommendation, replayRun, type ReplayRecommendation } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { RecommendationSummary } from "@/components/replay-modal/recommendation-summary";
import { ResumePromptEditor } from "@/components/replay-modal/resume-prompt-editor";
import { SteeringInput } from "@/components/replay-modal/steering-input";

export function ReplayModal({
  runId,
  nodeId,
  open,
  onOpenChange,
}: {
  runId: string;
  nodeId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [recommendation, setRecommendation] = useState<ReplayRecommendation | null>(null);
  const [prompt, setPrompt] = useState("");
  const [steering, setSteering] = useState("");

  useEffect(() => {
    if (!open || !nodeId) return;
    getReplayRecommendation(runId, nodeId).then((value) => {
      setRecommendation(value);
      setPrompt(value?.generated_resume_prompt ?? "");
    });
  }, [nodeId, open, runId]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Replay from node</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <RecommendationSummary recommendation={recommendation} />
          <ResumePromptEditor value={prompt} onChange={setPrompt} />
          <SteeringInput value={steering} onChange={setSteering} />
        </div>
        <DialogFooter>
          <Button disabled={!nodeId} onClick={() => nodeId && replayRun(runId, { node_id: nodeId, edited_resume_prompt: prompt, user_context: steering }).then(() => onOpenChange(false))}>
            Start replay
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
