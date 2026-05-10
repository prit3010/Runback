import { createStore } from "zustand/vanilla";
import { useStore } from "zustand";
import type { SseEvent } from "@/lib/sse-types";
import { createEmptyDagState, dagReducer, type DagState } from "@/lib/store/dag-reducer";
import type { components } from "@/lib/api-types";

type RunDag = components["schemas"]["RunDag"];

export interface DagStore {
  state: DagState;
  selectedNodeId: string | null;
  visibleBranches: Set<string> | null;
  collapsedGroups: Set<string>;
  loadSnapshot: (snapshot: RunDag) => void;
  applyEvent: (event: SseEvent) => void;
  selectNode: (nodeId: string | null) => void;
  toggleGroup: (groupId: string) => void;
  setVisibleBranches: (branches: Set<string> | null) => void;
}

export function createDagStore(runId = "pending") {
  return createStore<DagStore>((set) => ({
    state: createEmptyDagState(runId),
    selectedNodeId: null,
    visibleBranches: null,
    collapsedGroups: new Set(),
    loadSnapshot: (snapshot) =>
      set({
        state: {
          runId: snapshot.run.id,
          nodes: Object.fromEntries(snapshot.nodes.map((node) => [node.id, node])),
          edges: Object.fromEntries(snapshot.edges.map((edge) => [edge.id, edge])),
          checkpoints: Object.fromEntries(snapshot.checkpoints.map((checkpoint) => [checkpoint.id, checkpoint])),
          groups: Object.fromEntries(snapshot.groups.map((group) => [group.id, { ...group, collapsed: false }])),
          sideEffects: snapshot.side_effects ?? [],
          branches: Array.from(new Set([...snapshot.nodes.map((node) => node.branch_id), ...snapshot.edges.map((edge) => edge.branch_id)])),
        },
      }),
    applyEvent: (event) => set((current) => ({ state: dagReducer(current.state, event) })),
    selectNode: (nodeId) => set({ selectedNodeId: nodeId }),
    toggleGroup: (groupId) =>
      set((current) => {
        const next = new Set(current.collapsedGroups);
        if (next.has(groupId)) next.delete(groupId);
        else next.add(groupId);
        return { collapsedGroups: next };
      }),
    setVisibleBranches: (branches) => set({ visibleBranches: branches }),
  }));
}

export const dagStore = createDagStore();

export function useDagStore<T>(selector: (store: DagStore) => T): T {
  return useStore(dagStore, selector);
}
