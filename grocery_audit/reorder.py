"""Suggested orders from real sell-through, capped to the weekly budget."""
from __future__ import annotations

import math
from dataclasses import dataclass

from . import config
from .catalog import primary_vendor_item
from .models import SKU, AuditLine, VendorItem


@dataclass
class OrderLine:
    sku: str
    name: str
    vendor: str
    vendor_item_code: str
    cases: int
    units: float
    unit: str
    units_per_case: float
    est_cost: float
    daily_velocity: float
    perishable: bool
    note: str = ""


def suggest_orders(
    skus: dict[str, SKU],
    audit: list[AuditLine],
    vendor_map: dict[tuple[str, str], VendorItem],
    days: int,
) -> list[OrderLine]:
    """Order enough to cover lead time + time until the next order + safety stock.
    TODO: use 4-week average velocity instead of one week, and bump for holidays
    (Lunar New Year, Chuseok, Thanksgiving)."""
    orders = []
    for line in audit:
        sku = skus[line.sku]
        item = primary_vendor_item(line.sku, vendor_map)
        if item is None:
            continue
        daily = line.sold / days
        review = config.REVIEW_PERIOD_DAYS.get(sku.category, config.DEFAULT_REVIEW_PERIOD_DAYS)
        target = daily * (sku.lead_time_days + review + config.SAFETY_STOCK_DAYS)
        on_hand = line.counted_on_hand if line.counted_on_hand is not None else line.expected_on_hand
        need = target - on_hand
        if need <= 0:
            continue
        cases = math.ceil(need / item.units_per_case)
        units = cases * item.units_per_case
        orders.append(OrderLine(
            sku=line.sku, name=sku.name, vendor=item.vendor,
            vendor_item_code=item.vendor_item_code, cases=cases, units=units,
            unit=sku.unit, units_per_case=item.units_per_case, est_cost=round(units * sku.unit_cost, 2), daily_velocity=round(daily, 2),
            perishable=sku.perishable,
        ))
    return orders


def apply_budget(orders: list[OrderLine], budget: float) -> list[OrderLine]:
    """If the week's orders run over budget, fund the biggest sellers (by $ per day) first
    and mark the rest 'held'. Held lines stay in the list so the owner sees them.
    TODO: never cut a fast mover below one week of cover; drop slow dry goods first."""
    if sum(o.est_cost for o in orders) <= budget:
        return orders
    spent = 0.0
    ranked = sorted(orders, key=lambda o: o.daily_velocity * o.est_cost / o.units, reverse=True)
    for o in ranked:
        if spent + o.est_cost <= budget:
            spent += o.est_cost
        else:
            o.note = "held: over weekly budget"
    return ranked
