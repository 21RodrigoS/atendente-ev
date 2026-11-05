from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import Product, init_db, make_engine, seed_products

SEED = Path("data/products.json")


def _session():
    engine = make_engine("sqlite://")
    init_db(engine)
    return Session(engine)


def test_seed_is_idempotent():
    with _session() as s:
        assert seed_products(s, SEED) == 8
        assert seed_products(s, SEED) == 0


def test_prices_in_cents():
    with _session() as s:
        seed_products(s, SEED)
        price = {p.slug: p.price_cents for p in s.scalars(select(Product))}
    assert price["maracuja"] == 2000
    assert price["acerola"] == 1400
