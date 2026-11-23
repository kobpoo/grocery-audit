"""Record types shared by every step of the pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SKU:
    sku: str
    name: str
    category: str          # produce | meat | seafood | refrigerated | frozen | dry
    unit: str              # how the POS sells it: "each" or "lb"
    perishable: bool
    lead_time_days: int    # days from placing an order to it hitting the back room
    unit_cost: float       # cost per store unit (per each, or per lb)


@dataclass(frozen=True)
class VendorItem:
    """One vendor's item code mapped to our SKU. Vendors never use our numbers."""
    vendor: str
    vendor_item_code: str
    sku: str
    units_per_case: float  # 1 CS soy sauce = 12 each; meat/produce invoiced by lb = 1


@dataclass
class InvoiceLine:
    vendor: str
    invoice_no: str
    invoice_date: date
    vendor_item_code: str
    description: str
    qty: float
    uom: str                                 # CS | EA | LB, as printed on the invoice
    unit_price: float
    sku: str | None = None                   # set by invoice_parser.match_to_skus
    qty_in_store_units: float | None = None  # set by the case -> each/lb conversion


@dataclass(frozen=True)
class POSSale:
    sale_date: date
    sku: str
    qty: float             # units, or lbs for scale items (meat, produce)
    net_sales: float


@dataclass
class AuditLine:
    """One SKU's result for the week."""
    sku: str
    name: str
    category: str
    unit: str
    start_on_hand: float
    received: float
    sold: float
    waste: float
    expected_on_hand: float
    counted_on_hand: float | None
    variance: float | None = None       # counted - expected (negative = missing stock)
    variance_pct: float | None = None
    flagged: bool = False
    reason: str = ""
