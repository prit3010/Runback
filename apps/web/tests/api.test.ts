import { describe, expect, it } from "vitest";
import { apiUrl, listFlows, listRuns, getRunDag, getReplayRecommendation } from "@/lib/api";

describe("api client helpers", () => {
  it("builds API URLs from NEXT_PUBLIC_BACKEND_URL", () => {
    expect(apiUrl("/api/runs", "http://localhost:8000")).toBe("http://localhost:8000/api/runs");
  });

  it("returns empty arrays for unimplemented list endpoints", async () => {
    const fetcher = async () => new Response(null, { status: 501 });
    await expect(listRuns(fetcher)).resolves.toEqual([]);
    await expect(listFlows(fetcher)).resolves.toEqual([]);
  });

  it("does not send JSON content-type on GET requests", async () => {
    let init: RequestInit | undefined;
    const fetcher = async (_input: RequestInfo | URL, requestInit?: RequestInit) => {
      init = requestInit;
      return Response.json([]);
    };
    await listRuns(fetcher);
    expect(init?.headers).toBeUndefined();
  });

  it("throws useful errors for failed entity endpoints", async () => {
    const fetcher = async () => new Response("nope", { status: 500 });
    await expect(getRunDag("run_1", fetcher)).rejects.toThrow("GET /api/runs/run_1/dag failed: 500");
  });

  it("passes nodeId as a replay recommendation query param", async () => {
    const seen: string[] = [];
    const fetcher = async (input: RequestInfo | URL) => {
      seen.push(String(input));
      return Response.json({
        source_node_id: "node_1",
        recommended_checkpoint_id: "cp_1",
        confidence: 0.8,
        reason: ["nearest checkpoint"],
        reuse_node_ids: [],
        rerun_node_ids: ["node_1"],
        approval_node_ids: [],
        unsafe_node_ids: [],
        generated_resume_prompt: "resume",
      });
    };

    await getReplayRecommendation("run_1", "node_1", fetcher);

    expect(seen[0]).toContain("/api/runs/run_1/replay/recommendation?node_id=node_1");
  });
});
