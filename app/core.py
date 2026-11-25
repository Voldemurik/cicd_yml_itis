"""Tiny data-processing app. This starter intentionally has formatting and logic errors."""

from decimal import Decimal


def make_metric(rows, mode):
    if mode == "row_count":
        return str(len(rows))
    if mode == "quantity_sum":
        return str(sum(int(row["quantity"]) for row in rows))
    if mode == "revenue":
        value = sum(
            (int(row["quantity"]) * Decimal(row["price"]) for row in rows), Decimal("0")
        )
        return str(value)
    if mode == "max_price":
        return str(max((Decimal(row["price"]) for row in rows), default=Decimal("0")))
    if mode == "unique_categories":
        return str(len({row["category"] for row in rows}))
    if mode == "active_count":
        return str(sum(row["status"] == "active" for row in rows))
    raise ValueError(f"Unknown mode: {mode}")
