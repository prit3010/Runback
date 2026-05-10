import { beforeEach, describe, expect, it, vi } from "vitest";
import { RunEventStream } from "@/lib/sse-client";
import type { SseEvent } from "@/lib/sse-types";

class FakeEventSource {
  static instances: FakeEventSource[] = [];
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: (() => void) | null = null;
  url: string;
  closed = false;

  constructor(url: string) {
    this.url = url;
    FakeEventSource.instances.push(this);
  }

  emit(event: SseEvent) {
    this.onmessage?.({ data: JSON.stringify(event) } as MessageEvent);
  }

  fail() {
    this.onerror?.();
  }

  close() {
    this.closed = true;
  }
}

describe("RunEventStream", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    FakeEventSource.instances = [];
    vi.stubGlobal("EventSource", FakeEventSource);
  });

  it("dispatches typed SSE events", () => {
    const events: SseEvent[] = [];
    const stream = new RunEventStream("run_1", (event) => events.push(event), "http://api");

    FakeEventSource.instances[0].emit({
      type: "node.updated",
      run_id: "run_1",
      ts: "2026-05-09T00:00:00Z",
      payload: { node_id: "node_1", status: "success" },
    });

    expect(events[0]?.type).toBe("node.updated");
    stream.close();
  });

  it("reconnects with exponential backoff after errors", () => {
    const stream = new RunEventStream("run_1", vi.fn(), "http://api", { baseDelayMs: 100, maxDelayMs: 500 });

    FakeEventSource.instances[0].fail();
    expect(FakeEventSource.instances[0].closed).toBe(true);
    vi.advanceTimersByTime(99);
    expect(FakeEventSource.instances).toHaveLength(1);
    vi.advanceTimersByTime(1);
    expect(FakeEventSource.instances).toHaveLength(2);

    FakeEventSource.instances[1].fail();
    vi.advanceTimersByTime(200);
    expect(FakeEventSource.instances).toHaveLength(3);
    stream.close();
  });
});
