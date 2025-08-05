import { renderHook } from "@testing-library/react";
import { useAnalytics } from "../../../main/frontend/src/app/hooks/useAnalytics";

describe("useAnalytics hook", () => {
  it("initializes with empty data", () => {
    const { result } = renderHook(() => useAnalytics());
    expect(result.current.plateFrequency).toEqual([]);
    expect(result.current.accuracyTrends).toEqual([]);
  });
});
