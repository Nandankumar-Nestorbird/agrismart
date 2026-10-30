# Copyright (c) 2026, Nandan Kumar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class InventoryItem(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		category: DF.Literal["Seed", "Fertilizer", "Equipment", "Tool"]
		current_stock: DF.Float
		item_name: DF.Data
		reorder_level: DF.Float
		uom: DF.Literal["kg", "Liters", "Bags", "Pieces", "Boxes"]
	# end: auto-generated types

	_DOCTYPE_NAME = "Inventory Item"

	def validate(self):
		if self.reorder_level is None or self.reorder_level <= 0:
			frappe.throw(_("Reorder level must be greater than zero."))

		if self.current_stock is None:
			self.current_stock = 0

		if self.current_stock < 0:
			frappe.throw(_("Current stock cannot be negative."))
   
		if self.custom_target_stock_level is None or self.custom_target_stock_level <= 0:
			frappe.throw(_("Target Stock Level must be greater than zero."))

		if self.custom_target_stock_level <= self.reorder_level:
			frappe.throw(
				_("Target Stock Level must be greater than Reorder Level.")
			)
