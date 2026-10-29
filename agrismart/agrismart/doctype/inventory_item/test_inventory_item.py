# Copyright (c) 2026, Nandan Kumar and Contributors

import frappe
from frappe.tests import IntegrationTestCase


class IntegrationTestInventoryItem(IntegrationTestCase):

    def create_item(self, reorder_level=20, current_stock=0):
        item = frappe.get_doc({
            "doctype": "Inventory Item",
            "item_name": f"Test Seeds {frappe.generate_hash(length=6)}",
            "category": "Seed",
            "uom": "kg",
            "reorder_level": reorder_level,
            "current_stock": current_stock,
        })
        return item

    def test_reorder_level_must_be_positive(self):
        item = self.create_item(reorder_level=0)

        with self.assertRaises(frappe.ValidationError):
            item.insert(ignore_permissions=True)

    def test_negative_reorder_level_is_rejected(self):
        item = self.create_item(reorder_level=-5)

        with self.assertRaises(frappe.ValidationError):
            item.insert(ignore_permissions=True)

    def test_negative_current_stock_is_rejected(self):
        item = self.create_item(
            reorder_level=20,
            current_stock=-10,
        )

        with self.assertRaises(frappe.ValidationError):
            item.insert(ignore_permissions=True)

    def test_valid_inventory_item_can_be_created(self):
        item = self.create_item(
            reorder_level=20,
            current_stock=50,
        )

        item.insert(ignore_permissions=True)

        self.assertEqual(item.reorder_level, 20)
        self.assertEqual(item.current_stock, 50)

    def test_missing_current_stock_defaults_to_zero(self):
        item = self.create_item(
            reorder_level=20,
            current_stock=None,
        )

        item.insert(ignore_permissions=True)

        self.assertEqual(item.current_stock, 0)
