import type { SseEvent } from "@/lib/sse-types";
import { apiUrl } from "@/lib/api";

interface StreamOptions {
  baseDelayMs?: number;
  maxDelayMs?: number;
}

export class RunEventStream {
  private source: EventSource | null = null;
  private retryAttempt = 0;
  private retryTimer: ReturnType<typeof setTimeout> | null = null;
  private closed = false;
  private readonly baseDelayMs: number;
  private readonly maxDelayMs: number;

  constructor(
    private readonly runId: string,
    private readonly onEvent: (event: SseEvent) => void,
    private readonly baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000",
    options: StreamOptions = {},
  ) {
    this.baseDelayMs = options.baseDelayMs ?? 1_000;
    this.maxDelayMs = options.maxDelayMs ?? 30_000;
    this.connect();
  }

  close() {
    this.closed = true;
    if (this.retryTimer) clearTimeout(this.retryTimer);
    this.source?.close();
    this.source = null;
  }

  private connect() {
    if (this.closed) return;
    const source = new EventSource(apiUrl(`/api/runs/${this.runId}/events`, this.baseUrl));
    this.source = source;
    source.onmessage = (message) => {
      this.retryAttempt = 0;
      this.onEvent(JSON.parse(message.data) as SseEvent);
    };
    source.onerror = () => {
      source.close();
      if (this.closed) return;
      const delay = Math.min(this.maxDelayMs, this.baseDelayMs * 2 ** this.retryAttempt);
      this.retryAttempt += 1;
      this.retryTimer = setTimeout(() => this.connect(), delay);
    };
  }
}
