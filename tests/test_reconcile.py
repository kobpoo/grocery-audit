"""python -m unittest discover tests"""
import unittest
from datetime import date

from grocery_audit.invoice_parser import match_to_skus
from grocery_audit.models import SKU, InvoiceLine, POSSale, VendorItem
from grocery_audit.reconcile import reconcile

BOK_CHOY = SKU("1004", "Shanghai Bok Choy", "produce", "lb", True, 2, 1.05)
SOY = SKU("1002", "Light Soy Sauce 500 ml", "dry", "each", False, 7, 2.10)


def invoice(code, qty, uom):
    return InvoiceLine("v", "INV1", date(2026, 11, 17), code, "", qty, uom, 1.0)


class ReconcileTests(unittest.TestCase):
    def test_short_produce_is_flagged(self):
        # 40 start + 60 received - 70 sold - 6 waste = 24 expected; counted 19 -> 21% short
        lines, _ = match_to_skus([invoice("BOK", 60, "LB")], {("v", "BOK"): VendorItem("v", "BOK", "1004", 1)})
        sales = [POSSale(date(2026, 11, 18), "1004", 70, 139.30)]
        audit = reconcile({"1004": BOK_CHOY}, {"1004": 40}, {"1004": 19}, lines, sales, {"1004": 6})
        self.assertEqual(audit[0].expected_on_hand, 24)
        self.assertEqual(audit[0].variance, -5)
        self.assertTrue(audit[0].flagged)

    def test_cases_convert_to_eaches(self):
        lines, _ = match_to_skus([invoice("SOY", 2, "CS")], {("v", "SOY"): VendorItem("v", "SOY", "1002", 12)})
        self.assertEqual(lines[0].qty_in_store_units, 24)

    def test_one_unit_miss_not_flagged(self):
        audit = reconcile({"1002": SOY}, {"1002": 36}, {"1002": 35}, [], [], {})
        self.assertFalse(audit[0].flagged)

    def test_unknown_vendor_code_is_unmatched(self):
        matched, unmatched = match_to_skus([invoice("NEW-CODE", 2, "CS")], {})
        self.assertEqual((len(matched), len(unmatched)), (0, 1))

    # TODO: random-weight meat, negative (credit) invoice lines, SKU with no opening count


if __name__ == "__main__":
    unittest.main()
