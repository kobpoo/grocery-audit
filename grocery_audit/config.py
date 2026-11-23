"""Store settings. Change numbers here, not inside the modules."""

# How far off a SKU can be before it gets flagged, as a share of expected on-hand.
# Produce and meat get more room for trim, moisture loss and random-weight packs.
VARIANCE_TOLERANCE = {
    "produce": 0.10,
    "meat": 0.08,
    "seafood": 0.08,
    "refrigerated": 0.04,
    "frozen": 0.03,
    "dry": 0.02,
}
DEFAULT_TOLERANCE = 0.03
MIN_UNITS_TO_FLAG = 2  # don't flag a 1-unit miss on a slow mover

# Reordering. Produce and meat come twice a week; everything else weekly.
REVIEW_PERIOD_DAYS = {"produce": 3, "meat": 3, "seafood": 3}
DEFAULT_REVIEW_PERIOD_DAYS = 7
SAFETY_STOCK_DAYS = 2

# Weekly purchasing cap while revenue is down. TODO: set the real number with the owners.
WEEKLY_PURCHASE_BUDGET = 2500.00

# Before/after numbers need this many weeks on each side before they're reported.
BASELINE_WEEKS = 4
RECENT_WEEKS = 4

OUTPUT_DIR = "output"
