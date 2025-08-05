import { renderHook, act } from "@testing-library/react";
import { useUploader } from "../../../main/frontend/src/app/hooks/useUploader";

describe("useUploader hook", () => {
  it("starts with empty files", () => {
    const { result } = renderHook(() => useUploader());
    expect(result.current.files).toEqual([]);
  });

  it("updates files state", () => {
    const { result } = renderHook(() => useUploader());
    act(() => {
      result.current.setFiles([new File([], "file.jpg")]);
    });
    expect(result.current.files.length).toBe(1);
  });
});
