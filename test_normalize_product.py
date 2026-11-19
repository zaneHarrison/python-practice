import copy

import pytest

from normalize_product import InvalidProductError, NormalizedProduct, normalize_product

# A valid record in each retailer format. Error tests change exactly one field.
AMAZON = {
    "merchant": "Amazon",
    "sku": "B08N5WRWNW",
    "name": "  Sony WH-1000XM5 Wireless Headphones ",
    "brand": " Sony ",
    "price": "299.99",
    "currency": "usd",
    "url": "https://example.com/product",
}

BEST_BUY = {
    "retailer": "Best Buy",
    "product_id": "BB12345",
    "title": "Sony WH1000XM5 Headphones",
    "manufacturer": "Sony",
    "price": 279.99,
    "currency": "USD",
}


def without(record: dict, key: str) -> dict:
    return {k: v for k, v in record.items() if k != key}


# --- Happy paths ---


def test_amazon_format():
    assert normalize_product(AMAZON) == NormalizedProduct(
        retailer="Amazon",
        retailer_sku="B08N5WRWNW",
        title="Sony WH-1000XM5 Wireless Headphones",
        price=299.99,
        currency="USD",
        brand="Sony",
        url="https://example.com/product",
    )


def test_best_buy_format():
    assert normalize_product(BEST_BUY) == NormalizedProduct(
        retailer="Best Buy",
        retailer_sku="BB12345",
        title="Sony WH1000XM5 Headphones",
        price=279.99,
        currency="USD",
        brand="Sony",
        url=None,
    )


def test_sku_as_int_is_converted():
    assert normalize_product({**AMAZON, "sku": 99931}).retailer_sku == "99931"


def test_zero_price_is_allowed():
    assert normalize_product({**AMAZON, "price": 0}).price == 0.0


@pytest.mark.parametrize("field", ["brand", "url"])
def test_optional_field_missing(field):
    assert getattr(normalize_product(without(AMAZON, field)), field) is None


def test_optional_field_blank():
    assert normalize_product({**AMAZON, "brand": "   "}).brand is None


def test_input_not_mutated():
    original = copy.deepcopy(AMAZON)
    normalize_product(AMAZON)
    assert AMAZON == original


# --- Missing required fields ---


@pytest.mark.parametrize(
    "key, field",
    [
        ("merchant", "retailer"),
        ("sku", "retailer_sku"),
        ("name", "title"),
        ("price", "price"),
        ("currency", "currency"),
    ],
)
def test_missing_required_field(key, field):
    with pytest.raises(InvalidProductError, match=f"Missing or blank '{field}'"):
        normalize_product(without(AMAZON, key))


@pytest.mark.parametrize("value", ["", "   "])
def test_blank_required_field(value):
    with pytest.raises(InvalidProductError, match="Missing or blank 'retailer'"):
        normalize_product({**AMAZON, "merchant": value})


# --- Invalid values ---


@pytest.mark.parametrize(
    "price, reason",
    [
        ("not a number!", "can't parse"),
        ([279.99], "can't parse"),
        (True, "bool"),
        (-5, "negative"),
        ("NaN", "finite"),
        (float("nan"), "finite"),
        ("inf", "finite"),
        ("-inf", "finite"),
    ],
)
def test_invalid_price(price, reason):
    with pytest.raises(InvalidProductError, match=reason):
        normalize_product({**AMAZON, "price": price})


@pytest.mark.parametrize(
    "key, field, value",
    [
        ("merchant", "retailer", 123),
        ("name", "title", 123),
        ("currency", "currency", 840),
        ("brand", "brand", ["Sony"]),
        ("url", "url", 42),
    ],
)
def test_non_string_field(key, field, value):
    with pytest.raises(InvalidProductError, match=f"'{field}' must be a string"):
        normalize_product({**AMAZON, key: value})


def test_errors_are_value_errors():
    # Callers that catch ValueError still work
    with pytest.raises(ValueError):
        normalize_product({**AMAZON, "price": "abc"})
