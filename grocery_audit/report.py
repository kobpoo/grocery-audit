"""Write the week's files and print the summary the owner reads at the register."""
from __future__ import annotations

import csv
from dataclasses import asdict
from pathlib import Path

from .bottlenecks import Bottleneck
from .models import AuditLine
from .reorder import OrderLine


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_week(out_dir: Path, audit: list[AuditLine], orders: list[OrderLine],
               bottlenecks: list[Bottleneck]) -> None:
    """TODO: one Excel workbook with tabs instead of loose CSVs (openpyxl)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(out_dir / "audit.csv", [asdict(l) for l in audit])
    _write_csv(out_dir / "discrepancies.csv", [asdict(l) for l in audit if l.flagged])
    _write_csv(out_dir / "reorder.csv", [asdict(o) for o in orders])
    (out_dir / "bottlenecks.txt").write_text(
        "\n".join(f"[{b.kind}] {b.detail}" for b in bottlenecks) + "\n", encoding="utf-8")


def print_summary(week_label: str, audit: list[AuditLine], orders: list[OrderLine],
                  bottlenecks: list[Bottleneck], metrics_lines: list[str], out_dir: Path) -> None:
    flagged = [l for l in audit if l.flagged]
    funded = [o for o in orders if not o.note]
    print(f"\n=== Inventory audit, week of {week_label} ===")
    print(f"SKUs audited: {len(audit)}   flagged: {len(flagged)}")
    for l in flagged:
        print(f"  ! {l.sku} {l.name:<32} {l.reason}")
    print(f"\nBottlenecks ({len(bottlenecks)}):")
    for b in bottlenecks:
        print(f"  - [{b.kind}] {b.detail}")
    print(f"\nSuggested orders: {len(funded)} lines, ${sum(o.est_cost for o in funded):,.2f}"
          + (f"  ({len(orders) - len(funded)} held for budget)" if len(funded) < len(orders) else ""))
    for o in orders:
        qty = (f"{o.cases} cs = {o.units:g} {o.unit}" if o.units_per_case > 1
               else f"{o.units:g} {o.unit}")
        print(f"  {o.vendor:<20} {o.vendor_item_code:<10} {o.name:<30} {qty:<18} ${o.est_cost:>8,.2f} {o.note}")
    print("\nTracking:")
    for m in metrics_lines:
        print(f"  {m}")
    print(f"\nFiles: {out_dir}")
