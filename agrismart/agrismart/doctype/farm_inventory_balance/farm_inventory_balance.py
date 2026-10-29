# Copyright (c) 2026, Nandan Kumar and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class FarmInventoryBalance(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		current_stock: DF.Float
		farm: DF.Link
		inventory_item: DF.Link
	# end: auto-generated types

	_DOCTYPE_NAME = "Farm Inventory Balance"
