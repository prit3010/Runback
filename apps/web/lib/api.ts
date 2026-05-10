import type { components } from "@/lib/api-types";

export type Flow = components["schemas"]["Flow"];
export type FlowCreate = components["schemas"]["FlowCreate"];
export type Run = components["schemas"]["Run"];
export type RunDag = components["schemas"]["RunDag"];
export type NodeDetail = components["schemas"]["NodeDetail"];
export type Runner = components["schemas"]["Runner"];
export type ReplayAttempt = components["schemas"]["ReplayAttempt"];
export type ReplayRecommendation = components["schemas"]["ReplayRecommendation"];
export type PolicyOverride = components["schemas"]["PolicyOverride"];

type Fetcher = typeof fetch;

export function apiUrl(path: string, base?: string) {
  if (base) return new URL(path, base).toString();
  if (typeof window !== "undefined") return path;
  return new URL(path, process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000").toString();
}

async function readJson<T>(response: Response, fallback: T): Promise<T> {
  if (response.status === 501) return fallback;
  if (!response.ok) throw new Error(`${response.url ? response.url.replace(apiUrl("", ""), "") : "Request"} failed: ${response.status}`);
  if (response.status === 204) return fallback;
  return (await response.json()) as T;
}

async function request<T>(path: string, fallback: T, fetcher: Fetcher = fetch, init?: RequestInit): Promise<T> {
  const headers = init?.body ? { "content-type": "application/json", ...(init?.headers ?? {}) } : init?.headers;
  const response = await fetcher(apiUrl(path), {
    headers,
    ...init,
  });
  if (response.status === 501) return fallback;
  if (!response.ok) throw new Error(`${init?.method ?? "GET"} ${path} failed: ${response.status}`);
  return readJson<T>(response, fallback);
}

export function listFlows(fetcher?: Fetcher) {
  return request<Flow[]>("/api/flows", [], fetcher);
}

export function getFlow(flowId: string, fetcher?: Fetcher) {
  return request<Flow | null>(`/api/flows/${flowId}`, null, fetcher);
}

export function createFlow(body: FlowCreate, fetcher?: Fetcher) {
  return request<Flow | null>("/api/flows", null, fetcher, { method: "POST", body: JSON.stringify(body) });
}

export function listRuns(fetcher?: Fetcher) {
  return request<Run[]>("/api/runs", [], fetcher);
}

export function getRun(runId: string, fetcher?: Fetcher) {
  return request<Run | null>(`/api/runs/${runId}`, null, fetcher);
}

export function getRunDag(runId: string, fetcher?: Fetcher) {
  return request<RunDag | null>(`/api/runs/${runId}/dag`, null, fetcher);
}

export function getNode(runId: string, nodeId: string, fetcher?: Fetcher) {
  return request<NodeDetail | null>(`/api/runs/${runId}/nodes/${nodeId}`, null, fetcher);
}

export function listRunners(fetcher?: Fetcher) {
  return request<Runner[]>("/api/runners", [], fetcher);
}

export function getReplayRecommendation(runId: string, nodeId: string, fetcher?: Fetcher) {
  return request<ReplayRecommendation | null>(
    `/api/runs/${runId}/replay/recommendation?node_id=${encodeURIComponent(nodeId)}`,
    null,
    fetcher,
  );
}

export function replayRun(runId: string, body: { node_id: string; user_context?: string; edited_resume_prompt?: string }, fetcher?: Fetcher) {
  return request<ReplayAttempt | null>(`/api/runs/${runId}/replay`, null, fetcher, { method: "POST", body: JSON.stringify(body) });
}

export function overrideNodePolicy(runId: string, nodeId: string, body: PolicyOverride, fetcher?: Fetcher) {
  return request<null>(`/api/runs/${runId}/nodes/${nodeId}/policy`, null, fetcher, {
    method: "POST",
    body: JSON.stringify(body),
  });
}
