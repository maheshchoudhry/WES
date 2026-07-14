import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { knowledgeApi } from "../api/knowledge";
import { KnowledgeLibrary } from "../pages/knowledge/KnowledgeLibrary";

// Keep the real DOC_TYPES / docTypeLabel helpers; only mock the API surface.
vi.mock("../api/knowledge", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/knowledge")>();
  return {
    ...actual,
    knowledgeApi: { documents: vi.fn(), categories: vi.fn() },
  };
});

beforeEach(() => {
  vi.mocked(knowledgeApi.documents).mockResolvedValue({
    data: [
      {
        id: "k1",
        code: "KB-0002",
        slug: "kb-0002",
        title: "Backend Coding Standard",
        doc_type: "coding_standard",
        category_id: "c1",
        category_name: "Engineering",
        summary: "Conventions",
        status: "approved",
        version: 1,
        tags: ["backend", "standard"],
        is_pinned: false,
        view_count: 12,
        author_id: null,
        approver_id: null,
        updated_at: null,
        created_at: null,
      },
    ],
    meta: { total: 1 },
  } as never);
  vi.mocked(knowledgeApi.categories).mockResolvedValue({
    data: [
      {
        id: "c1",
        code: "KC-ENGINEERING",
        name: "Engineering",
        description: null,
        parent_id: null,
        position: 0,
        document_count: 1,
      },
    ],
    meta: { total: 1 },
  } as never);
});

describe("KnowledgeLibrary", () => {
  it("lists documents with type, status, and tags", async () => {
    render(
      <MemoryRouter>
        <KnowledgeLibrary />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("Backend Coding Standard")).toBeInTheDocument());
    expect(screen.getByText("KB-0002")).toBeInTheDocument();
    // "Coding Standard" appears both as a filter option and the row's type cell.
    expect(screen.getAllByText("Coding Standard").length).toBeGreaterThan(0);
    expect(screen.getByText("approved")).toBeInTheDocument();
    expect(screen.getByText("backend, standard")).toBeInTheDocument();
  });
});
