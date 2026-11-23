"""Find where the inventory process breaks down, not just which numbers are off."""
from __future__ import annotations

from dataclasses import dataclass

from .models import SKU, AuditLine, InvoiceLine


@dataclass
class Bottleneck:
    kind: str
    sku: str | None
    detail: str


def unmatched_invoice_lines(unmatched: list[InvoiceLine]) -> list[Bottleneck]:
    """Invoice lines with a vendor code we have no mapping for (new item, or the
    vendor renumbered it). This stock is invisible to the audit until it's mapped."""
    return [
        Bottleneck("unmapped vendor code", None,
                   f"{l.vendor} {l.vendor_item_code} '{l.description}' x{l.qty:g} {l.uom} "
                   f"(invoice {l.invoice_no}): add to vendor_item_map.csv")
        for l in unmatched
    ]


def stockout_risk(skus: dict[str, SKU], audit: list[AuditLine], days: int) -> list[Bottleneck]:
    """SKUs that will run out before a new order can arrive."""
    out = []
    for line in audit:
        on_hand = line.counted_on_hand if line.counted_on_hand is not None else line.expected_on_hand
        daily = line.sold / days
        if daily <= 0:
            continue
        cover = on_hand / daily
        lead = skus[line.sku].lead_time_days
        if cover < lead:
            out.append(Bottleneck("stockout risk", line.sku,
                                  f"{line.name}: {cover:.1f} days on hand, lead time {lead} days"))
    return out


def repeat_offenders(history_dir, weeks: int = 3) -> list[Bottleneck]:
    """SKUs flagged in 3+ of the last N weeks: a process problem, not a one-off.
    TODO: read output/<week>/audit.csv for past weeks and count flags per SKU."""
    return []


def perishable_overstock(skus: dict[str, SKU], audit: list[AuditLine], days: int) -> list[Bottleneck]:
    """Perishables with more days on hand than shelf life: money going in the dumpster.
    TODO: add a shelf_life_days column to skus.csv, then compare to days of cover."""
    return []


def vendor_short_ships(invoices: list[InvoiceLine]) -> list[Bottleneck]:
    """Invoiced qty vs what receiving actually checked in at the back door.
    TODO: needs a receiving log (who counted the delivery, what they counted)."""
    return []


def find_all(skus, audit, matched, unmatched, days, history_dir) -> list[Bottleneck]:
    return (unmatched_invoice_lines(unmatched)
            + stockout_risk(skus, audit, days)
            + repeat_offenders(history_dir)
            + perishable_overstock(skus, audit, days)
            + vendor_short_ships(matched))
