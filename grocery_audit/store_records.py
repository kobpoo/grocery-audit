"""Load the store's own records: POS sales, shelf counts, and the waste log."""
from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date
from pathlib import Path

from .models import POSSale


def load_pos_sales(path: Path, week_start: date, week_end: date) -> list[POSSale]:
    """POS item-sales export, one row per item per day.
    TODO: map these column names to whatever the store's POS actually exports.
    TODO: if the POS uses PLU numbers that differ from SKUs, add a PLU -> SKU map."""
    sales = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            d = date.fromisoformat(row["date"])
            if week_start <= d < week_end:
                sales.append(POSSale(d, row["item_id"], float(row["qty"]), float(row["net_sales"])))
    return sales


def load_counts(path: Path, on: date) -> dict[str, float]:
    """Physical shelf + back-room count taken on a given date."""
    with open(path, newline="", encoding="utf-8") as f:
        return {
            row["sku"]: float(row["on_hand"])
            for row in csv.DictReader(f)
            if date.fromisoformat(row["count_date"]) == on
        }


def load_waste(path: Path, week_start: date, week_end: date) -> dict[str, float]:
    """Logged spoilage and trim (wilted produce, meat trim, damaged cans)."""
    waste: dict[str, float] = defaultdict(float)
    if not path.exists():
        return waste
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if week_start <= date.fromisoformat(row["date"]) < week_end:
                waste[row["sku"]] += float(row["qty"])
    return waste
