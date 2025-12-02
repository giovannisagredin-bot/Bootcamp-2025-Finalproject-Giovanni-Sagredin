from fastapi.testclient import TestClient

def test_create_prompt(client: TestClient):
    prompt_data = {
        "purpose": "summarize",
        "name": "Summarization Prompt",
        "template": "Please summarize the following text: {{text}}"
    }
    response = client.post("/v1/prompts", json=prompt_data)
    assert response.status_code == 200
    data = response.json()
    assert data["purpose"] == prompt_data["purpose"]
    assert data["name"] == prompt_data["name"]
    assert data["template"] == prompt_data["template"]
    assert data["version"] == 1
    assert data["active"] is True