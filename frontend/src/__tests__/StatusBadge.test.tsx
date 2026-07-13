import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StatusBadge } from "../components/StatusBadge";

describe("StatusBadge", () => {
  it("renders the status label with a matching class", () => {
    const { container } = render(<StatusBadge status="active" />);
    expect(screen.getByText("active")).toBeInTheDocument();
    expect(container.querySelector(".badge-active")).not.toBeNull();
  });
});
