"""Weekly run:  python -m grocery_audit --week-start 2026-11-16 [--data data/sample]"""
from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path

from . import bottlenecks, config, metrics, reorder, report
from .catalog import load_skus, load_vendor_map
from .invoice_parser import match_to_skus, parse_invoice_folder
from .reconcile import reconcile
from .store_records import load_counts, load_pos_sales, load_waste

DAYS = 7


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="grocery_audit",
                                description="Vendor invoices vs POS sales vs shelf counts, weekly.")
    p.add_argument("--week-start", required=True, type=date.fromisoformat,
                   help="date of the opening count, YYYY-MM-DD")
    p.add_argument("--data", type=Path, default=Path("data/sample"))
    args = p.parse_args(argv)

    week_start, data = args.week_start, args.data
    week_end = week_start + timedelta(days=DAYS)
    out_dir = Path(config.OUTPUT_DIR) / week_start.isoformat()

    # 1. Load
    skus = load_skus(data / "skus.csv")
    vendor_map = load_vendor_map(data / "vendor_item_map.csv")
    invoice_lines = parse_invoice_folder(data / "invoices", week_start, week_end)
    matched, unmatched = match_to_skus(invoice_lines, vendor_map)
    sales = load_pos_sales(data / "pos_export.csv", week_start, week_end)
    waste = load_waste(data / "waste_log.csv", week_start, week_end)
    start_counts = load_counts(data / "counts.csv", week_start)
    end_counts = load_counts(data / "counts.csv", week_end)

    # 2. Audit, find bottlenecks, plan reorders
    audit = reconcile(skus, start_counts, end_counts, matched, sales, waste)
    found = bottlenecks.find_all(skus, audit, matched, unmatched, DAYS, Path(config.OUTPUT_DIR))
    orders = reorder.apply_budget(reorder.suggest_orders(skus, audit, vendor_map, DAYS),
                                  config.WEEKLY_PURCHASE_BUDGET)

    # 3. Track and report
    history = metrics.update_history(Path(config.OUTPUT_DIR) / "metrics_history.csv",
                                     metrics.week_summary(week_start, audit, skus))
    metrics_lines = [
        f"Discrepancy trend: {metrics.discrepancy_change(history)}",
        f"Audit time: {metrics.hours_saved(data / 'time_log.csv')}",
    ]
    report.write_week(out_dir, audit, orders, found)
    report.print_summary(week_start.isoformat(), audit, orders, found, metrics_lines, out_dir)


if __name__ == "__main__":
    main()
