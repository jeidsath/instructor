import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiFetch, ApiError } from "../../api/client";

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

describe("apiFetch", () => {
  it("prepends /api to path and returns parsed JSON", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ id: "1", name: "Test" }));

    const result = await apiFetch<{ id: string; name: string }>("/learners/1");

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/learners/1",
      expect.objectContaining({ headers: {} }),
    );
    expect(result).toEqual({ id: "1", name: "Test" });
  });

  it("sets Content-Type for POST requests", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ id: "1", name: "Test" }, 201));

    await apiFetch("/learners", {
      method: "POST",
      body: JSON.stringify({ name: "Test" }),
    });

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/learners",
      expect.objectContaining({
        headers: { "Content-Type": "application/json" },
      }),
    );
  });

  it("throws ApiError with status and body on 404", async () => {
    mockFetch.mockResolvedValue(
      jsonResponse({ detail: "Not found" }, 404),
    );

    try {
      await apiFetch("/learners/missing");
      expect.fail("should have thrown");
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      const err = e as ApiError;
      expect(err.status).toBe(404);
      expect(err.body).toEqual({ detail: "Not found" });
    }
  });

  it("throws ApiError with status and body on 422", async () => {
    const validationError = {
      detail: [{ loc: ["body", "name"], msg: "field required", type: "value_error.missing" }],
    };
    mockFetch.mockResolvedValue(jsonResponse(validationError, 422));

    await expect(apiFetch("/learners")).rejects.toThrow(ApiError);
  });

  it("throws on network error", async () => {
    mockFetch.mockRejectedValue(new TypeError("Failed to fetch"));

    await expect(apiFetch("/learners")).rejects.toThrow("Failed to fetch");
  });
});
