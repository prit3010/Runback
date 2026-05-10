import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export function SteeringInput({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return (
    <div className="space-y-2">
      <Label htmlFor="steering">Additional steering</Label>
      <Textarea id="steering" value={value} onChange={(event) => onChange(event.target.value)} placeholder="Optional context for the replay" />
    </div>
  );
}
