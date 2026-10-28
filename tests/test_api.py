import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

TEST_DB = Path("/tmp/simple_product_catalog_test.db")
TEST_DB.unlink(missing_ok=True)
os.environ["DATABASE_FILE"] = str(TEST_DB)

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def sample(sku: str, category: str = "shoes", price: int = 10000) -> dict:
    return {
        "sku": sku,
        "name": f"Product {sku}",
        "category": category,
        "price_cents": price,
        "description": "Test product",
    }


def test_product_crud():
    created = client.post("/products", json=sample("CRUD-1"))
    assert created.status_code == 201
    product_id = created.json()["id"]

    fetched = client.get(f"/products/{product_id}")
    assert fetched.status_code == 200
    assert fetched.json()["sku"] == "CRUD-1"

    updated_data = sample("CRUD-1", price=12000)
    updated = client.put(f"/products/{product_id}", json=updated_data)
    assert updated.status_code == 200
    assert updated.json()["price_cents"] == 12000

    deleted = client.delete(f"/products/{product_id}")
    assert deleted.status_code == 204
    assert client.get(f"/products/{product_id}").status_code == 404


def test_filtering_and_pagination():
    client.post("/products", json=sample("RUN-1", "running", 5000))
    client.post("/products", json=sample("RUN-2", "running", 7000))
    client.post("/products", json=sample("RUN-3", "running", 9000))
    client.post("/products", json=sample("BASKET-1", "basketball", 6000))

    response = client.get(
        "/products",
        params={
            "category": "running",
            "min_price_cents": 5000,
            "max_price_cents": 8000,
            "page": 1,
            "page_size": 1,
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["total"] == 2
    assert len(result["items"]) == 1
    assert result["items"][0]["sku"] == "RUN-1"
