import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import DomainTree from "./DomainTree";

describe("DomainTree", () => {
  it("renders nested domains as nested links", () => {
    render(
      <MemoryRouter>
        <DomainTree
          nodes={[
            {
              slug: "math",
              title: "Math",
              children: [
                { slug: "algebra", title: "Algebra", children: [] },
              ],
            },
            { slug: "cs", title: "Computer Science", children: [] },
          ]}
        />
      </MemoryRouter>,
    );
    expect(screen.getByText("Math")).toBeInTheDocument();
    expect(screen.getByText("Algebra")).toBeInTheDocument();
    expect(screen.getByText("Computer Science")).toBeInTheDocument();
    const algebraLink = screen.getByText("Algebra").closest("a");
    expect(algebraLink?.getAttribute("href")).toBe("/d/algebra");
  });
});
