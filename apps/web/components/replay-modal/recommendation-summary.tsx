import type { ReplayRecommendation } from "@/lib/api";

export function RecommendationSummary({ recommendation }: { recommendation: ReplayRecommendation | null }) {
  if (!recommendation) return <p className="text-sm text-muted-foreground">No recommendation available.</p>;
  return (
    <div className="rounded-md border p-3 text-sm">
      <div className="font-medium">Checkpoint {recommendation.recommended_checkpoint_id}</div>
      <div className="text-muted-foreground">Confidence {Math.round(recommendation.confidence * 100)}%</div>
      <ul className="mt-2 list-disc pl-4">
        {recommendation.reason.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
