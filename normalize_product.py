import math
from dataclasses import dataclass
from typing import Any

NORMALIZED_PRODUCT_FIELD_TO_KEYS = {
    "retailer": ["merchant", "retailer"],
    "retailer_sku": ["sku", "product_id"],
    "title": ["title", "name"],
    "brand": ["brand", "manufacturer"],
    "price": ["price"],
    "currency": ["currency"],
    "url": ["url"],
}


class InvalidProductError(ValueError):
    """Raised when a raw product record can't be normalized."""


@dataclass(frozen=True)
class NormalizedProduct:
    retailer: str
    retailer_sku: str
    title: str
    price: float
    currency: str
    brand: str | None = None
    url: str | None = None


def get_from_keys(obj: dict, field: str, required: bool = True) -> Any:
    keys = NORMALIZED_PRODUCT_FIELD_TO_KEYS[field]
    for key in keys:
        value = obj.get(key)
        if isinstance(value, str):
            value = value.strip()
        if value is not None and value != "":
            return value
    if required:
        raise InvalidProductError(
            f"Missing or blank '{field}'. Expected one of {keys}, got keys {list(obj.keys())}"
        )
    return None


def get_str(obj: dict, field: str, required: bool = True) -> str | None:
    value = get_from_keys(obj, field, required)
    if value is not None and not isinstance(value, str):
        raise InvalidProductError(
            f"'{field}' must be a string, got {type(value).__name__}: {value!r}"
        )
    return value


def validate_price(price: Any) -> float:
    if isinstance(price, bool):
        raise InvalidProductError(f"Invalid price: bool is not a price ({price!r})")
    try:
        price_float = float(price)
    except (TypeError, ValueError) as e:
        raise InvalidProductError(f"Invalid price: can't parse {price!r}") from e
    if not math.isfinite(price_float):
        raise InvalidProductError(f"Invalid price: must be finite, got {price!r}")
    if price_float < 0:
        raise InvalidProductError(f"Invalid price: must not be negative, got {price!r}")
    return price_float


def normalize_product(raw: dict) -> NormalizedProduct:
    return NormalizedProduct(
        retailer=get_str(raw, "retailer"),
        # SKUs are often numeric, so convert rather than reject
        retailer_sku=str(get_from_keys(raw, "retailer_sku")),
        title=get_str(raw, "title"),
        price=validate_price(get_from_keys(raw, "price")),
        currency=get_str(raw, "currency").upper(),
        brand=get_str(raw, "brand", required=False),
        url=get_str(raw, "url", required=False),
    )
