# Simple Product Catalog API

This is a small interview exercise showing a REST API for an e-commerce product catalog.

## What it does

- Create a product
- Get a product by ID
- Update a product
- Delete a product
- List products
- Filter by category and minimum/maximum price
- Paginate results with `page` and `page_size`

## Technology choice

I used **Python and FastAPI** because the code is short and the API documentation is generated automatically.

The demo uses **SQLite**, so it can run without installing a database server. For a real service containing hundreds of thousands of products, I would use **PostgreSQL** with the same relational model. PostgreSQL is a good fit because products have a clear structure and clients need reliable filtering by category and price.

Prices are stored as integer cents instead of decimal numbers, which avoids rounding problems.

## Run the project

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Open `http://127.0.0.1:8000/docs` to try the API in a browser.

Run the tests:

```bash
pytest -q
```

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/products` | Create a product |
| GET | `/products/{id}` | Get one product |
| GET | `/products` | List and filter products |
| PUT | `/products/{id}` | Update a product |
| DELETE | `/products/{id}` | Delete a product |

Example list request:

```text
GET /products?category=running&min_price_cents=5000&max_price_cents=15000&page=1&page_size=20
```

## Basic scalability choices

- The database has indexes on `category` and `price_cents`, because those are the main filters.
- Pagination prevents the API from returning the entire catalog in one response.
- Page size is limited to 100.
- For production, I would run PostgreSQL and multiple API instances behind a load balancer.
- If traffic becomes much larger, frequently read products could be cached and PostgreSQL read replicas could be added. I would add these only after monitoring shows they are needed.

The solution is intentionally simple. It demonstrates the requested API behavior without adding production patterns that are unnecessary for a short interview exercise.
