# Copyright (c) 2026, Nandan Kumar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class StockTransaction(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		farm: DF.Link
		inventory_item: DF.Link
		quantity: DF.Float
		remarks: DF.SmallText | None
		transaction_date: DF.Date
		transaction_type: DF.Literal["Stock In", "Stock Out"]
	# end: auto-generated types

	_DOCTYPE_NAME = "Stock Transaction"

	def validate(self):
		if not self.transaction_date:
			frappe.throw(_("Transaction date is required."))

		if not self.farm or not self.inventory_item:
			frappe.throw(_("Farm and inventory item are required."))

		if self.quantity is None or self.quantity <= 0:
			frappe.throw(_("Quantity must be greater than zero."))

		if self.transaction_type not in ("Stock In", "Stock Out"):
			frappe.throw(_("Invalid transaction type."))

	def on_submit(self):
		self.apply_stock_movement(
			self.transaction_type,
			self.quantity
		)

	def on_cancel(self):
		reverse_type = (
			"Stock Out"
			if self.transaction_type == "Stock In"
			else "Stock In"
		)

		self.apply_stock_movement(
			reverse_type,
			self.quantity
		)

	def apply_stock_movement(self, movement_type, quantity):
		item = frappe.get_doc(
			"Inventory Item", self.inventory_item
		)

		# Lock the item row to prevent concurrent stock updates
		frappe.db.sql(
			"""
			SELECT name
			FROM `tabInventory Item`
			WHERE name = %s
			FOR UPDATE
			""",
			(self.inventory_item,),
		)

		balance_name = frappe.db.get_value(
			"Farm Inventory Balance",
			{
				"farm": self.farm,
				"inventory_item": self.inventory_item,
			},
			"name",
		)

		if balance_name:
			balance = frappe.get_doc(
				"Farm Inventory Balance", balance_name
			)
		else:
			balance = frappe.get_doc({
				"doctype": "Farm Inventory Balance",
				"farm": self.farm,
				"inventory_item": self.inventory_item,
				"current_stock": 0,
			})

		farm_stock = balance.current_stock or 0
		total_stock = item.current_stock or 0

		if movement_type == "Stock In":
			farm_stock += quantity
			total_stock += quantity
		else:
			if farm_stock < quantity:
				frappe.throw(
					_("Insufficient stock at the selected farm.")
				)

			if total_stock < quantity:
				frappe.throw(
					_("Insufficient total inventory stock.")
				)

			farm_stock -= quantity
			total_stock -= quantity

		balance.current_stock = farm_stock
		balance.save(ignore_permissions=True)

		item.current_stock = total_stock
		item.save(ignore_permissions=True)
