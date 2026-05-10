import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ArtifactViewer } from "@/components/artifact-viewer";

describe("ArtifactViewer", () => {
  it("renders markdown artifacts as text content", () => {
    render(<ArtifactViewer artifact={{ type: "markdown", content_preview: "# Report" }} />);
    expect(screen.getByText(/Report/)).toBeInTheDocument();
  });
});
