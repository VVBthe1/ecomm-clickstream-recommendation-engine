from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app


def test_health_or_unavailable():
    client = TestClient(app)
    resp = client.get("/health")
    # 200 if models exist; 503 if not trained yet
    assert resp.status_code in (200, 503)
    if resp.status_code == 200:
        body = resp.json()
        assert body["status"] == "ok"
        assert "model_loaded" in body
        assert "gold_data_range" in body


def test_predict_unknown_product():
    client = TestClient(app)
    health = client.get("/health")
    if health.status_code != 200:
        return  # skip when models not present
    resp = client.post(
        "/predict",
        json={"product_id": -1, "date": "2019-11-16"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["note"] is not None
    assert "no data" in body["note"]


def test_predict_known_row_if_available():
    client = TestClient(app)
    health = client.get("/health")
    if health.status_code != 200:
        return
    products = client.get("/products?limit=1")
    assert products.status_code == 200
    items = products.json()
    if not items:
        return
    pid = items[0]["product_id"]
    date = health.json()["gold_data_range"]["max_date"]
    # Prefer a late-Nov train feature day if present
    for candidate in ("2019-11-15", "2019-11-16", date):
        resp = client.post("/predict", json={"product_id": pid, "date": candidate})
        assert resp.status_code == 200
        body = resp.json()
        if body.get("note") is None:
            assert isinstance(body["predicted_purchases_next_day"], float)
            assert body["features_used"]
            assert "actual_purchases_next_day" in body
            if body["actual_purchases_next_day"] is not None:
                assert body["prediction_error"] == (
                    body["predicted_purchases_next_day"]
                    - body["actual_purchases_next_day"]
                )
            return


def test_top_predicted_for_date():
    client = TestClient(app)
    health = client.get("/health")
    if health.status_code != 200:
        return
    date = "2019-11-16"
    resp = client.get(f"/top?date={date}&limit=10")
    assert resp.status_code == 200
    body = resp.json()
    assert body["date"] == date
    assert body["count"] == 10
    assert len(body["products"]) == 10
    preds = [p["predicted_purchases_next_day"] for p in body["products"]]
    assert preds == sorted(preds, reverse=True)
    assert body["products"][0]["rank"] == 1


def test_top_predicted_unknown_date():
    client = TestClient(app)
    health = client.get("/health")
    if health.status_code != 200:
        return
    resp = client.get("/top?date=2099-01-01&limit=10")
    assert resp.status_code == 404
