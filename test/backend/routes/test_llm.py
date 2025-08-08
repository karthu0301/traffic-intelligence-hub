from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main.backend.main import app

client = TestClient(app)

@patch("main.backend.services.llm.run_llm_task.apply_async")
def test_ask_llm(mock_apply_async):
    mock_task = MagicMock()
    mock_task.id = "mocked_id"
    mock_apply_async.return_value = mock_task

    res = client.post("/ask", json={"question": "What is AI?"})
    assert res.status_code == 200
    assert res.json() == {"message": "LLM processing started", "task_id": "mocked_id"}

    mock_apply_async.assert_called_once()
