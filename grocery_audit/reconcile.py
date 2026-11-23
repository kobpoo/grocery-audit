"""The audit itself: what should be on the shelf vs. what was counted.

    expected_end = start_count + received (invoices) - sold (POS) - logged waste
    variance     = counted_end - expected_end      (negative = stock went missing)
"""
from __future__ import annotations

from collections import defaultdict

from . import config
from .models import SKU, AuditLine, InvoiceLine, POSSale


def reconcile(
    skus: dict[str, SKU],
    start_counts: dict[str, float],
    end_counts: dict[str, float],
    received_lines: list[InvoiceLine],
    sales: list[POSSale],
    waste: dict[str, float],
) -> list[AuditLine]:
    received: dict[str, float] = defaultdict(float)
    for line in received_lines:
        received[line.sku] += line.qty_in_store_units

    sold: dict[str, float] = defaultdict(float)
    for s in sales:
        sold[s.sku] += s.qty

    results = []
    for sku_id, sku in skus.items():
        start = start_counts.get(sku_id)
        if start is None:
            # TODO: no opening count -> fall back to last week's expected close?
            continue
        expected = start + received[sku_id] - sold[sku_id] - waste.get(sku_id, 0.0)
        line = AuditLine(
            sku=sku_id, name=sku.name, category=sku.category, unit=sku.unit,
            start_on_hand=start, received=received[sku_id], sold=sold[sku_id],
            waste=waste.get(sku_id, 0.0), expected_on_hand=round(expected, 2),
            counted_on_hand=end_counts.get(sku_id),
        )
        if line.counted_on_hand is not None:
            line.variance = round(line.counted_on_hand - line.expected_on_hand, 2)
            line.variance_pct = (line.variance / line.expected_on_hand
                                 if line.expected_on_hand > 0 else None)
            line.flagged, line.reason = flag_reason(line)
        results.append(line)
    return results


def flag_reason(line: AuditLine) -> tuple[bool, str]:
    if abs(line.variance) < config.MIN_UNITS_TO_FLAG:
        return False, ""
    if line.expected_on_hand <= 0:
        return True, "system expects none on hand: missing invoice or wrong case size?"
    tolerance = config.VARIANCE_TOLERANCE.get(line.category, config.DEFAULT_TOLERANCE)
    if abs(line.variance_pct) <= tolerance:
        return False, ""
    direction = "short" if line.variance < 0 else "over"
    # TODO: guess the likely cause per pattern, e.g. 'over' by exactly one case = unmatched
    # invoice; 'short' every week on meat = trim not being logged; POS ringing the wrong PLU.
    return True, (f"{direction} {abs(line.variance):g} {line.unit} "
                  f"({abs(line.variance_pct):.0%} vs {tolerance:.0%} allowed)")
