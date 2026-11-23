"""Load the master SKU list and the vendor item-code map."""
from __future__ import annotations

import csv
from pathlib import Path

from .models import SKU, VendorItem


def load_skus(path: Path) -> dict[str, SKU]:
    with open(path, newline="", encoding="utf-8") as f:
        return {
            row["sku"]: SKU(
                sku=row["sku"],
                name=row["name"],
                category=row["category"],
                unit=row["unit"],
                perishable=row["perishable"].strip().lower() == "true",
                lead_time_days=int(row["lead_time_days"]),
                unit_cost=float(row["unit_cost"]),
            )
            for row in csv.DictReader(f)
        }


def load_vendor_map(path: Path) -> dict[tuple[str, str], VendorItem]:
    """Keyed by (vendor, vendor_item_code)."""
    with open(path, newline="", encoding="utf-8") as f:
        items = [
            VendorItem(
                vendor=row["vendor"],
                vendor_item_code=row["vendor_item_code"],
                sku=row["sku"],
                units_per_case=float(row["units_per_case"]),
            )
            for row in csv.DictReader(f)
        ]
    return {(i.vendor, i.vendor_item_code): i for i in items}


def primary_vendor_item(sku: str, vendor_map: dict[tuple[str, str], VendorItem]) -> VendorItem | None:
    """The vendor we reorder this SKU from.
    TODO: when two vendors carry the same SKU, pick by price or lead time instead of first match."""
    return next((i for i in vendor_map.values() if i.sku == sku), None)
