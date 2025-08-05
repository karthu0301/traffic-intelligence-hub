import { renderHook, act } from "@testing-library/react";
import { useDetectionData } from "../../../main/frontend/src/app/hooks/useDetection";

describe("useDetectionData hook", () => {
  it("initializes correctly", () => {
    const { result } = renderHook(() => useDetectionData());
    expect(result.current.history).toEqual([]);
    expect(result.current.result).toBeNull();
  });

  it("can set search term", () => {
    const { result } = renderHook(() => useDetectionData());
    act(() => result.current.setSearchTerm("ABC"));
    expect(result.current.searchTerm).toBe("ABC");
  });
});
