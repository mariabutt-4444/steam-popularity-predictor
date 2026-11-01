import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "service" in data

def test_get_all_stats(client):
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 8  # we have 9 tables
    table_names = [item["table_name"] for item in data]
    assert "summary_stats" in table_names
    assert "popularity_tier_distribution" in table_names

def test_get_specific_stat_table(client):
    response = client.get("/api/stats/popularity_tier_distribution")
    assert response.status_code == 200
    data = response.json()
    assert data["table_name"] == "popularity_tier_distribution"
    assert "insight" in data
    assert "columns" in data
    assert "rows" in data
    assert len(data["rows"]) > 0

def test_get_nonexistent_stat_table(client):
    response = client.get("/api/stats/non_existent_table")
    assert response.status_code == 404

def test_get_games_list(client):
    response = client.get("/api/games?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert len(data["items"]) <= 10
    assert data["total"] > 0

def test_filter_games_by_tier(client):
    response = client.get("/api/games?tier=High&page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    for game in data["items"]:
        assert game["popularity_tier"] == "High"

def test_get_game_details(client):
    # Fetch first game from games list
    list_res = client.get("/api/games?page=1&page_size=1")
    first_game = list_res.json()["items"][0]
    appid = first_game["appid"]

    detail_res = client.get(f"/api/games/{appid}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["appid"] == appid
    assert "genres" in detail
    assert "categories" in detail
    assert "platforms" in detail

def test_get_nonexistent_game(client):
    response = client.get("/api/games/999999999")
    assert response.status_code == 404

def test_get_rejected_games(client):
    response = client.get("/api/rejected")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_predict_placeholder_501(client):
    payload = {
        "price": 19.99,
        "genres": ["Action", "Indie"],
        "platforms": ["windows", "mac"],
        "release_month": 6
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 501
    assert "Project 2" in response.json()["detail"]
