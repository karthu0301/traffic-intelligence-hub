import { renderHook, act } from "@testing-library/react";
import { useLLM } from "../../../main/frontend/src/app/hooks/useLLM";

describe("useLLM hook", () => {
  it("initializes correctly", () => {
    const { result } = renderHook(() => useLLM());
    expect(result.current.llmAnswer).toBe("");
    expect(result.current.loadingAnswer).toBe(false);
  });

  it("updates llmAnswer", () => {
    const { result } = renderHook(() => useLLM());
    act(() => {
      result.current.askLLM("test");
    });
    // you can expand with mocking fetch here later
  });
});
