from backend.services.llm import build_prompt

def test_build_prompt():
    prompt = build_prompt("Why did detection fail?", {"filename": "x.jpg", "detections": []})
    assert "detection fail" in prompt