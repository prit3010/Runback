import { BaseEdge, EdgeLabelRenderer, getBezierPath, type EdgeProps } from "@xyflow/react";

export function SequenceEdge(props: EdgeProps) {
  const [path, labelX, labelY] = getBezierPath(props);
  const isReplay = props.data?.edge_type === "replay_branch";
  return (
    <>
      <BaseEdge path={path} markerEnd={props.markerEnd} style={{ stroke: isReplay ? "#7c3aed" : "#71717a", strokeDasharray: isReplay ? "6 4" : undefined }} />
      {isReplay && (
        <EdgeLabelRenderer>
          <span className="pointer-events-none absolute rounded bg-purple-50 px-1 text-[10px] text-purple-700" style={{ transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)` }}>
            replay
          </span>
        </EdgeLabelRenderer>
      )}
    </>
  );
}
