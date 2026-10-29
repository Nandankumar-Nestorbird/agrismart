
# Copyright (c) 2026, Nandan Kumar and Contributors

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today


class IntegrationTestStockTransaction(IntegrationTestCase):

    def setUp(self):
        suffix = frappe.generate_hash(length=6)

        self.farm = frappe.get_doc({
            "doctype": "Farm",
            "farm_name": f"Test Farm {suffix}",
            "location": "Mohali",
            "farm_owner": "Administrator",
            "size_acres": 10,
            "soil_type": "Loamy",
        }).insert(ignore_permissions=True)

        self.item = frappe.get_doc({
            "doctype": "Inventory Item",
            "item_name": f"Test Seeds {suffix}",
            "category": "Seed",
            "uom": "kg",
            "reorder_level": 10,
            "current_stock": 0,
        }).insert(ignore_permissions=True)

    def create_transaction(self, transaction_type, quantity):
        return frappe.get_doc({
            "doctype": "Stock Transaction",
            "transaction_date": today(),
            "inventory_item": self.item.name,
            "farm": self.farm.name,
            "transaction_type": transaction_type,
            "quantity": quantity,
        })

    def get_farm_stock(self):
        return frappe.db.get_value(
            "Farm Inventory Balance",
            {
                "farm": self.farm.name,
                "inventory_item": self.item.name,
            },
            "current_stock",
        ) or 0

    def test_stock_in_increases_stock(self):
        transaction = self.create_transaction("Stock In", 100)
        transaction.insert(ignore_permissions=True)
        transaction.submit()

        self.item.reload()

        self.assertEqual(self.item.current_stock, 100)
        self.assertEqual(self.get_farm_stock(), 100)

    def test_stock_out_decreases_stock(self):
        stock_in = self.create_transaction("Stock In", 100)
        stock_in.insert(ignore_permissions=True)
        stock_in.submit()

        stock_out = self.create_transaction("Stock Out", 30)
        stock_out.insert(ignore_permissions=True)
        stock_out.submit()

        self.item.reload()

        self.assertEqual(self.item.current_stock, 70)
        self.assertEqual(self.get_farm_stock(), 70)

    def test_insufficient_stock_is_rejected(self):
        transaction = self.create_transaction("Stock Out", 10)
        transaction.insert(ignore_permissions=True)

        with self.assertRaises(frappe.ValidationError):
            transaction.submit()

        self.item.reload()

        self.assertEqual(self.item.current_stock, 0)
        self.assertEqual(self.get_farm_stock(), 0)

    def test_zero_quantity_is_rejected(self):
        transaction = self.create_transaction("Stock In", 0)

        with self.assertRaises(frappe.ValidationError):
            transaction.insert(ignore_permissions=True)

    def test_cancelling_stock_in_reverses_movement(self):
        transaction = self.create_transaction("Stock In", 25)
        transaction.insert(ignore_permissions=True)
        transaction.submit()

        transaction.cancel()

        self.item.reload()

        self.assertEqual(self.item.current_stock, 0)
        self.assertEqual(self.get_farm_stock(), 0)
