# grocery-audit

A weekly inventory audit for a family-run Asian supermarket. It puts three records side by side for every SKU:

1. **Vendor invoices**: what the distributors say they delivered (cases of soy sauce, pounds of pork belly, bunches of basil)
2. **POS sales**: what the register says was sold
3. **Shelf counts**: what was physically there at the start and end of the week

```
expected on hand = opening count + received (invoices) - sold (POS) - logged waste
variance         = closing count - expected on hand
```

A SKU gets flagged when the variance is bigger than its category allows. Produce and meat get more room than canned goods because of trim, moisture loss and random-weight packs. The audit also lists **bottlenecks**, meaning places where the process itself breaks down, and writes a **reorder list** sized to real sell-through and capped at a weekly budget.

## Run it

Requires Python 3.10+, standard library only.

```
python -m grocery_audit --week-start 2026-11-16 --data data/sample
python -m unittest discover tests
```

`--week-start` is the date of the opening count. `--data` points at a folder of input files (see below). `data/sample/` is an example week with 12 SKUs that shows each file's format.

Results go to `output/<week>/`: `audit.csv` (every SKU), `discrepancies.csv` (flagged only), `reorder.csv` and `bottlenecks.txt`. A summary prints to the terminal.

## Layout

```
grocery_audit/
  models.py          record types: SKU, VendorItem, InvoiceLine, POSSale, AuditLine
  config.py          tolerances, reorder periods, weekly budget
  catalog.py         master SKU list + vendor item-code map
  invoice_parser.py  vendor invoices -> lines matched to SKUs, cases converted to eaches/lbs
  store_records.py   POS export, shelf counts, waste log
  reconcile.py       the audit math and flag rules
  bottlenecks.py     unmapped vendor codes, stockout risk
  reorder.py         suggested orders rounded to case packs, budget cap
  metrics.py         week-over-week discrepancy rate and audit hours
  report.py          CSV output + terminal summary
  __main__.py        the weekly run
data/sample/         example week showing the input file formats
tests/               unittest cases for the audit math
```

## Input files (`data/<folder>/`)

| File | What it is | Where it comes from |
|---|---|---|
| `skus.csv` | master list: category, unit (each/lb), lead time, unit cost | built once, updated when items are added |
| `vendor_item_map.csv` | vendor's item code -> our SKU, units per case | built once per vendor; the audit tells you when a code is missing |
| `invoices/<vendor>_<date>.csv` | one file per delivery | vendor email / portal export |
| `pos_export.csv` | item sales per day | POS back office export |
| `counts.csv` | shelf + back-room counts | counted by hand at the start of each week |
| `waste_log.csv` | spoilage and trim | clipboard in the back, typed in |
| `time_log.csv` | minutes spent auditing each week, `manual` or `automated` | logged weekly |

## How the numbers get measured

`metrics.py` reports two numbers and won't print them until there's enough data:

- **Discrepancy trend:** share of audited SKUs flagged per week, average of the first 4 weeks vs the last 4. It needs 8 weeks of runs. The drop comes from fixing what the audit surfaces: mapping renumbered vendor codes, correcting case sizes, getting trim logged.
- **Audit hours:** average weekly minutes logged as `manual` (the old way) vs `automated`. The manual weeks are the baseline, so they get logged before switching over.

Each run updates `output/metrics_history.csv`, so the history builds up week by week.

## Roadmap

- [ ] PDF invoice parsing (`pdfplumber`), including non-English descriptions, credit lines and catch-weight lines
- [ ] Per-vendor column maps for each distributor's invoice export
- [ ] PLU -> SKU map for POS systems whose item numbers differ from SKUs
- [ ] Fuzzy-match suggestions for unmapped vendor codes (`difflib`)
- [ ] Likely-cause hints on flagged SKUs (off by exactly one case = unmatched invoice, etc.)
- [ ] Repeat-offender report across weeks, perishable overstock, vendor short-ships
- [ ] 4-week velocity and holiday bumps (Lunar New Year, Chuseok, Thanksgiving) in reorders
- [ ] Smarter budget trimming: protect fast movers, cut slow dry goods first
- [ ] Single Excel workbook output (`openpyxl`)
