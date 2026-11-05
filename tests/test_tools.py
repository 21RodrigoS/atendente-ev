from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import Order, OrderItem, init_db, make_engine, seed_products
from app.tools import (
    check_availability,
    create_order,
    find_product,
    get_price,
    normalize,
    run_tool,
)


@pytest.fixture
def s():
    engine = make_engine("sqlite://")
    init_db(engine)
    with Session(engine) as session:
        seed_products(session, Path("data/products.json"))
        yield session


def test_normalize():
    assert normalize("  MaracuJÁ ") == "maracuja"


def test_find_product_ignores_accent_and_case(s):
    assert find_product(s, "MARACUJA").slug == "maracuja"
    assert find_product(s, "maracujá").slug == "maracuja"


def test_unknown_flavor_returns_error(s):
    assert find_product(s, "jabuticaba") is None
    assert get_price(s, "jabuticaba")["ok"] is False
    assert check_availability(s, "jabuticaba")["ok"] is False


def test_price_common_2kg(s):
    assert get_price(s, "acerola", 2)["total_cents"] == 2800


def test_price_club_4kg_has_7_percent(s):
    assert get_price(s, "acerola", 4, club=True)["total_cents"] == 5208


def test_club_below_4kg_rejected(s):
    assert get_price(s, "acerola", 3, club=True)["ok"] is False


@pytest.mark.parametrize("kg", [0, -1, 0.1, 999])
def test_invalid_quantities(s, kg):
    assert get_price(s, "acerola", kg)["ok"] is False


def test_availability(s):
    assert check_availability(s, "graviola") == {"ok": True, "flavor": "Graviola", "in_stock": False}


def test_order_creates_rows(s):
    res = create_order(s, "sess", [{"flavor": "maracujá", "kg": 2}, {"flavor": "manga", "kg": 1}])
    assert res["ok"] is True
    assert res["total_cents"] == 4000 + 1400
    assert s.scalar(select(Order).where(Order.id == res["order_id"])).session_id == "sess"
    assert len(s.scalars(select(OrderItem)).all()) == 2


def test_order_out_of_stock_rejected(s):
    res = create_order(s, "sess", [{"flavor": "graviola", "kg": 1}])
    assert res["ok"] is False
    assert s.scalars(select(Order)).all() == []


def test_order_empty_or_invalid_rejected(s):
    assert create_order(s, "x", [])["ok"] is False
    assert create_order(s, "x", [{"flavor": "manga", "kg": 0}])["ok"] is False


def test_run_tool_unknown_name(s):
    assert run_tool(s, "x", "hack", {})["ok"] is False


def test_run_tool_bad_args(s):
    assert run_tool(s, "x", "get_price", {"wrong": 1})["ok"] is False


def test_run_tool_dispatches(s):
    assert run_tool(s, "x", "get_price", {"flavor": "manga", "kg": 1})["total_cents"] == 1400
