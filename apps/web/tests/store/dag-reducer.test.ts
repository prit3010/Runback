import { describe, expect, it } from "vitest";
import { createEmptyDagState, dagReducer } from "@/lib/store/dag-reducer";
import { createDagStore } from "@/lib/store/dag-store";

describe("dagReducer", () => {
  it("adds and updates nodes from SSE events", () => {
    const withNode = dagReducer(createEmptyDagState("run_1"), {
      type: "node.created",
      run_id: "run_1",
      ts: "2026-05-09T00:00:00Z",
      payload: {
        node_id: "node_1",
        branch_id: "branch_1",
        group_id: null,
        type: "tool",
        label: "npm test",
        tool_name: "Bash",
        recovery_policy: "rerun",
        status: "running",
      },
    });

    const updated = dagReducer(withNode, {
      type: "node.updated",
      run_id: "run_1",
      ts: "2026-05-09T00:00:01Z",
      payload: { node_id: "node_1", status: "failed", error: "boom" },
    });

    expect(updated.nodes.node_1.status).toBe("failed");
    expect(updated.nodes.node_1.error).toBe("boom");
  });

  it("tracks branches, replay edges, groups, checkpoints, and side effects", () => {
    let state = createEmptyDagState("run_1");
    state = dagReducer(state, {
      type: "group.opened",
      run_id: "run_1",
      ts: "2026-05-09T00:00:00Z",
      payload: { group_id: "group_1", parent_group_id: null, label: "Ticket #1", kind: "todo" },
    });
    state = dagReducer(state, {
      type: "edge.created",
      run_id: "run_1",
      ts: "2026-05-09T00:00:00Z",
      payload: {
        edge_id: "edge_1",
        branch_id: "branch_1",
        source_node_id: "a",
        target_node_id: "b",
        edge_type: "replay_branch",
      },
    });
    state = dagReducer(state, {
      type: "checkpoint.created",
      run_id: "run_1",
      ts: "2026-05-09T00:00:00Z",
      payload: { checkpoint_id: "cp_1", branch_id: "branch_1", label: "Before npm test", node_id: "a" },
    });
    state = dagReducer(state, {
      type: "side_effect.logged",
      run_id: "run_1",
      ts: "2026-05-09T00:00:00Z",
      payload: { node_id: "b", kind: "github.pr", idempotency_key: "key", status: "executed", external_ref: "https://example.test" },
    });

    expect(state.groups.group_1.label).toBe("Ticket #1");
    expect(state.edges.edge_1.edge_type).toBe("replay_branch");
    expect(state.checkpoints.cp_1.label).toBe("Before npm test");
    expect(state.sideEffects).toHaveLength(1);
  });
});

describe("createDagStore", () => {
  it("sets visible branches to filter replay branches", () => {
    const store = createDagStore();
    store.getState().setVisibleBranches(new Set(["root"]));
    expect(store.getState().visibleBranches?.has("root")).toBe(true);
    store.getState().setVisibleBranches(null);
    expect(store.getState().visibleBranches).toBeNull();
  });
});
