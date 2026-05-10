import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export function ResumePromptEditor({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return (
    <div className="space-y-2">
      <Label htmlFor="resume-prompt">Resume prompt</Label>
      <Textarea id="resume-prompt" value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}
