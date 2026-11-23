"""Read vendor invoices, match each line to a store SKU, convert cases to store units.

Each vendor sends invoices differently (CSV export, emailed PDF, paper), so every
file type gets its own parser in PARSERS. Files are named <vendor>_<YYYY-MM-DD>.<ext>.
"""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from .models import InvoiceLine, VendorItem

UOM_ALIASES = {
    "CS": "CS", "CASE": "CS", "BX": "CS", "BOX": "CS",
    "EA": "EA", "PC": "EA", "BUNCH": "EA",
    "LB": "LB", "LBS": "LB", "#": "LB",
}


def parse_csv_invoice(path: Path, vendor: str) -> list[InvoiceLine]:
    """Vendors that email a CSV export.
    TODO: per-vendor column maps once you have each vendor's real export headers."""
    lines = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            uom = row["uom"].strip().upper()
            lines.append(InvoiceLine(
                vendor=vendor,
                invoice_no=row["invoice_no"],
                invoice_date=date.fromisoformat(row["invoice_date"]),
                vendor_item_code=row["item_code"].strip(),
                description=row["description"],
                qty=float(row["qty"]),
                uom=UOM_ALIASES.get(uom, uom),
                unit_price=float(row["unit_price"]),
            ))
    return lines


def parse_pdf_invoice(path: Path, vendor: str) -> list[InvoiceLine]:
    """Vendors that only send PDFs.
    TODO: pdfplumber -> pull the line-item table -> same fields as parse_csv_invoice.
    Watch for: descriptions in Chinese/Korean/Vietnamese, credit lines (negative qty),
    and catch-weight lines (qty in cases, price per lb)."""
    raise NotImplementedError(f"PDF invoices not built yet: {path.name}")


PARSERS = {".csv": parse_csv_invoice, ".pdf": parse_pdf_invoice}


def vendor_from_filename(path: Path) -> str:
    """pacific_foods_2026-11-17.csv -> pacific_foods"""
    return path.stem.rsplit("_", 1)[0]


def parse_invoice_folder(folder: Path, week_start: date, week_end: date) -> list[InvoiceLine]:
    lines: list[InvoiceLine] = []
    for path in sorted(folder.iterdir()):
        parser = PARSERS.get(path.suffix.lower())
        if parser is None:
            continue
        lines += [l for l in parser(path, vendor_from_filename(path))
                  if week_start <= l.invoice_date < week_end]
    return lines


def to_store_units(line: InvoiceLine, item: VendorItem) -> float:
    if line.uom == "CS":
        return line.qty * item.units_per_case
    if line.uom in ("EA", "LB"):
        return line.qty
    raise ValueError(f"Unknown UOM {line.uom!r} on {line.vendor} invoice {line.invoice_no}")


def match_to_skus(
    lines: list[InvoiceLine], vendor_map: dict[tuple[str, str], VendorItem]
) -> tuple[list[InvoiceLine], list[InvoiceLine]]:
    """Returns (matched, unmatched). An unmatched line is stock that physically
    arrived but the audit can't see, so it shows up later as an 'over' variance."""
    matched, unmatched = [], []
    for line in lines:
        item = vendor_map.get((line.vendor, line.vendor_item_code))
        if item is None:
            # TODO: fuzzy-match the description (difflib) and suggest a mapping to approve
            unmatched.append(line)
            continue
        line.sku = item.sku
        line.qty_in_store_units = to_store_units(line, item)
        matched.append(line)
    return matched, unmatched
