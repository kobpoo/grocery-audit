"""The before/after numbers. Any figure that goes on a resume or application comes from here.

Every weekly run writes one row to output/metrics_history.csv. Time spent auditing is
logged by hand in data/time_log.csv (week_start, method, minutes), for both the old
clipboard-and-spreadsheet audit (method=manual) and this one (method=automated).
"""
from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date
from pathlib import Path
from statistics import mean

from . import config
from .models import SKU, AuditLine

HISTORY_FIELDS = ["week_start", "skus_audited", "skus_flagged", "discrepancy_rate", "abs_variance_value"]


def week_summary(week_start: date, audit: list[AuditLine], skus: dict[str, SKU]) -> dict:
    counted = [l for l in audit if l.variance is not None]
    flagged = [l for l in counted if l.flagged]
    return {
        "week_start": week_start.isoformat(),
        "skus_audited": len(counted),
        "skus_flagged": len(flagged),
        "discrepancy_rate": round(len(flagged) / len(counted), 4) if counted else 0.0,
        "abs_variance_value": round(sum(abs(l.variance) * skus[l.sku].unit_cost for l in counted), 2),
    }


def update_history(path: Path, row: dict) -> list[dict]:
    """Replace this week's row if the week is re-run, keep the file sorted by week."""
    rows = []
    if path.exists():
        with open(path, newline="", encoding="utf-8") as f:
            rows = [r for r in csv.DictReader(f) if r["week_start"] != row["week_start"]]
    rows.append({k: str(v) for k, v in row.items()})
    rows.sort(key=lambda r: r["week_start"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, HISTORY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def discrepancy_change(history: list[dict]) -> str:
    need = config.BASELINE_WEEKS + config.RECENT_WEEKS
    if len(history) < need:
        return f"not enough history yet: {len(history)} of {need} weeks"
    base = mean(float(r["discrepancy_rate"]) for r in history[:config.BASELINE_WEEKS])
    recent = mean(float(r["discrepancy_rate"]) for r in history[-config.RECENT_WEEKS:])
    if base == 0:
        return "baseline weeks had no discrepancies"
    return (f"{(base - recent) / base:.0%} fewer flagged SKUs per week "
            f"(first {config.BASELINE_WEEKS} wks avg {base:.1%} -> last {config.RECENT_WEEKS} wks avg {recent:.1%})")


def hours_saved(time_log: Path) -> str:
    if not time_log.exists():
        return "no time log yet: create data/time_log.csv"
    minutes_by_week: dict[str, dict[str, float]] = {"manual": defaultdict(float), "automated": defaultdict(float)}
    with open(time_log, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["method"] in minutes_by_week:
                minutes_by_week[row["method"]][row["week_start"]] += float(row["minutes"])
    manual, auto = minutes_by_week["manual"], minutes_by_week["automated"]
    if not manual or not auto:
        return (f"need logged weeks of both methods: {len(manual)} manual, {len(auto)} automated "
                "(log minutes in data/time_log.csv)")
    m, a = mean(manual.values()) / 60, mean(auto.values()) / 60
    return (f"{m - a:.1f} hrs/week saved (manual avg {m:.1f} hrs over {len(manual)} wks -> "
            f"automated avg {a:.1f} hrs over {len(auto)} wks)")
