import { describe, expect, it } from "vitest";
import type { components, paths } from "../lib/api-types";
import type { SseEvent } from "../lib/sse-types";

describe("api-types generation", () => {
  it("Run schema has required fields", () => {
    type Run = components["schemas"]["Run"];
    const sample: Run = {
      id: "run_1",
      run_kind: "ad_hoc",
      status: "running",
      original_prompt: "x",
      repo_path: "/tmp",
      root_branch_id: "b",
      current_branch_id: "b",
      created_at: "2026-05-09T00:00:00Z",
    };
    expect(sample.id).toBe("run_1");
  });

  it("paths includes /api/hooks/claude", () => {
    type HooksOp = paths["/api/hooks/claude"]["post"];
    const check: HooksOp extends object ? true : false = true;
    expect(check).toBe(true);
  });
});

describe("sse-types", () => {
  it("discriminated union narrows", () => {
    const evt: SseEvent = {
      type: "node.created",
      run_id: "r1",
      ts: "2026-05-09T00:00:00Z",
      payload: {
        node_id: "n1",
        branch_id: "b1",
        group_id: null,
        type: "tool",
        label: "x",
        tool_name: "Read",
        recovery_policy: "reuse_cached",
        status: "running",
      },
    };
    if (evt.type === "node.created") {
      expect(evt.payload.node_id).toBe("n1");
    }
  });
});
