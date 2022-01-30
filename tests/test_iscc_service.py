from starlette.testclient import TestClient
from iscc_service import __version__
from iscc_service.main import app


client = TestClient(app)


def test_version():
    assert __version__ == "1.1.0b15"


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert "ISCC Web Service API" in response.text


# def test_from_url():
#     response = client.post("/generate/from_url", params={"url": "https://iscc.codes"})
#     result = response.json()
#     assert result["title_trimmed"] == "iscc content identifiers"
