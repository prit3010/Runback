import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StatusPill } from "@/components/status-pill";

describe("StatusPill", () => {
  it("renders a running status with an accessible label", () => {
    render(<StatusPill status="running" />);
    expect(screen.getByText("running")).toBeInTheDocument();
  });
});
