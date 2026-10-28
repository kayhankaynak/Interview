import os
import sqlite3
from contextlib import closing

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

DATABASE_FILE = os.getenv("DATABASE_FILE", "catalog.db")

app = FastAPI(title="Product Catalog API", version="1.0")


class ProductInput(BaseModel):
    sku: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=100)
    price_cents: int = Field(ge=0)
    description: str | None = None


class Product(ProductInput):
    id: int


class ProductPage(BaseModel):
    items: list[Product]
    page: int
    page_size: int
    total: int


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables() -> None:
    with closing(connect()) as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price_cents INTEGER NOT NULL CHECK (price_cents >= 0),
                description TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_products_category
                ON products(category);
            CREATE INDEX IF NOT EXISTS idx_products_price
                ON products(price_cents);
            """
        )
        db.commit()


create_tables()


def row_to_product(row: sqlite3.Row) -> Product:
    return Product(**dict(row))


@app.post("/products", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductInput) -> Product:
    try:
        with closing(connect()) as db:
            cursor = db.execute(
                """
                INSERT INTO products (sku, name, category, price_cents, description)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    product.sku,
                    product.name,
                    product.category,
                    product.price_cents,
                    product.description,
                ),
            )
            db.commit()
            row = db.execute(
                "SELECT * FROM products WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="SKU already exists") from exc
    return row_to_product(row)


@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int) -> Product:
    with closing(connect()) as db:
        row = db.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return row_to_product(row)


@app.get("/products", response_model=ProductPage)
def list_products(
    category: str | None = None,
    min_price_cents: int | None = Query(default=None, ge=0),
    max_price_cents: int | None = Query(default=None, ge=0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ProductPage:
    if (
        min_price_cents is not None
        and max_price_cents is not None
        and min_price_cents > max_price_cents
    ):
        raise HTTPException(
            status_code=422,
            detail="min_price_cents cannot be greater than max_price_cents",
        )

    conditions = []
    parameters: list[str | int] = []

    if category:
        conditions.append("category = ?")
        parameters.append(category)
    if min_price_cents is not None:
        conditions.append("price_cents >= ?")
        parameters.append(min_price_cents)
    if max_price_cents is not None:
        conditions.append("price_cents <= ?")
        parameters.append(max_price_cents)

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    offset = (page - 1) * page_size

    with closing(connect()) as db:
        total = db.execute(
            "SELECT COUNT(*) FROM products" + where_clause,
            parameters,
        ).fetchone()[0]
        rows = db.execute(
            "SELECT * FROM products"
            + where_clause
            + " ORDER BY id LIMIT ? OFFSET ?",
            [*parameters, page_size, offset],
        ).fetchall()

    return ProductPage(
        items=[row_to_product(row) for row in rows],
        page=page,
        page_size=page_size,
        total=total,
    )


@app.put("/products/{product_id}", response_model=Product)
def update_product(product_id: int, product: ProductInput) -> Product:
    try:
        with closing(connect()) as db:
            cursor = db.execute(
                """
                UPDATE products
                SET sku = ?, name = ?, category = ?, price_cents = ?, description = ?
                WHERE id = ?
                """,
                (
                    product.sku,
                    product.name,
                    product.category,
                    product.price_cents,
                    product.description,
                    product_id,
                ),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Product not found")
            db.commit()
            row = db.execute(
                "SELECT * FROM products WHERE id = ?", (product_id,)
            ).fetchone()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="SKU already exists") from exc
    return row_to_product(row)


@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int) -> None:
    with closing(connect()) as db:
        cursor = db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Product not found")
        db.commit()
@app.get("/")
def root():
    return {
        "message": "Product Catalog API is running",
        "docs": "/docs"
    }