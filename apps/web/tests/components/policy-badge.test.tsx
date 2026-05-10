import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PolicyBadge } from "@/components/policy-badge";

describe("PolicyBadge", () => {
  it("renders the recovery policy label", () => {
    render(<PolicyBadge policy="reuse_cached" />);
    expect(screen.getByText("reuse cached")).toBeInTheDocument();
  });
});
