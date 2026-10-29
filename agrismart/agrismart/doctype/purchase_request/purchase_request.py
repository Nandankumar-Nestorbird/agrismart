# Copyright (c) 2026, Nandan Kumar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import getdate, today

class PurchaseRequest(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		farm: DF.Link
		inventory_item: DF.Link
		requested_quantity: DF.Float
		required_by_date: DF.Date
		status: DF.Literal["Draft", "Approved", "Ordered"]
	# end: auto-generated types

	_DOCTYPE_NAME = "Purchase Request"
 
	def validate(self):
		if (
			self.requested_quantity is None
			or self.requested_quantity <= 0
		):
			frappe.throw(
				_("Requested quantity must be greater than zero.")
			)

		if not self.required_by_date:
			frappe.throw(_("Required By Date is required."))

		if getdate(self.required_by_date) < getdate(today()):
			frappe.throw(
				_("Required By Date cannot be in the past.")
			)
