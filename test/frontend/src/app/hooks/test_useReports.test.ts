import { renderHook } from "@testing-library/react";
import { useReports } from "../../../main/frontend/src/app/hooks/useReports";

describe("useReports hook", () => {
  it("initializes correctly", () => {
    const { result } = renderHook(() => useReports("daily"));
    expect(result.current.report).toBe("");
    expect(result.current.loading).toBe(true);
  });
});
