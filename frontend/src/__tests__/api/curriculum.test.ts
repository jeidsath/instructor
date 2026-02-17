import { describe, it, expect, vi, beforeEach } from "vitest";
import { getVocabularySets, getGrammarConcepts } from "../../api/curriculum";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

beforeEach(() => {
  mockFetch.mockReset();
});

function jsonResponse(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("curriculum API", () => {
  it("getVocabularySets fetches /api/curriculum/:language/vocabulary", async () => {
    const sets = [
      { set_name: "core-1", language: "latin", item_count: 50 },
    ];
    mockFetch.mockResolvedValue(jsonResponse(sets));

    const result = await getVocabularySets("latin");

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/curriculum/latin/vocabulary",
      expect.anything(),
    );
    expect(result).toHaveLength(1);
    expect(result[0].set_name).toBe("core-1");
  });

  it("getGrammarConcepts fetches /api/curriculum/:language/grammar", async () => {
    const concepts = [
      {
        name: "first-declension",
        category: "morphology",
        subcategory: "nouns",
        difficulty_level: 1,
        prerequisite_names: [],
      },
    ];
    mockFetch.mockResolvedValue(jsonResponse(concepts));

    const result = await getGrammarConcepts("latin");

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/curriculum/latin/grammar",
      expect.anything(),
    );
    expect(result[0].name).toBe("first-declension");
  });
});
