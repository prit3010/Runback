import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { GridView } from "@/components/grid";

describe("GridView", () => {
  it("renders rows, run columns, and policy/status encoded cells", () => {
    render(
      <GridView
        rows={[{ id: "node_1", label: "npm test" }]}
        runs={[{ id: "run_1", label: "run 1" }]}
        cells={[{ rowId: "node_1", runId: "run_1", status: "reused", recoveryPolicy: "reuse_cached", nodeId: "node_1" }]}
      />,
    );

    expect(screen.getByText("npm test")).toBeInTheDocument();
    expect(screen.getByLabelText(/node_1 in run_1: reused, reuse_cached/i)).toBeInTheDocument();
  });
});
