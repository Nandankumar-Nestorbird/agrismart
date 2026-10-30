
import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import getdate, today, flt


class PurchaseRequest(Document):

	# begin: auto-generated types
	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		expected_stock: DF.Float
		farm: DF.Link
		inventory_item: DF.Link
		last_reminder_date: DF.Date | None
		pending_quantity: DF.Float
		received_quantity: DF.Float
		requested_quantity: DF.Float
		required_by_date: DF.Date
		status: DF.Literal["Draft", "Approved", "Ordered"]

	# end: auto-generated types

	_DOCTYPE_NAME = "Purchase Request"

	def validate(self):
		self.validate_requested_quantity()
		self.validate_received_quantity()
		self.validate_received_quantity_permission()
		self.validate_required_date()

		self.calculate_pending_quantity()
		self.calculate_expected_stock()

	def validate_requested_quantity(self):
		if flt(self.requested_quantity) <= 0:
			frappe.throw(
				_("Requested quantity must be greater than zero.")
			)

	def validate_received_quantity(self):
		received = flt(self.received_quantity)

		if received < 0:
			frappe.throw(
				_("Received quantity cannot be negative.")
			)

		if received > flt(self.requested_quantity):
			frappe.throw(
				_("Received quantity cannot exceed requested quantity.")
			)

	def validate_received_quantity_permission(self):
		if self.is_new():
			return

		old_doc = self.get_doc_before_save()

		if not old_doc:
			return

		old_received = flt(old_doc.received_quantity)
		new_received = flt(self.received_quantity)

		if (
			old_received != new_received
			and not self.flags.get("allow_received_quantity_update")
		):
			frappe.throw(
				_("Received Quantity can only be updated through Stock Transactions.")
			)

	def validate_required_date(self):
		if not self.required_by_date:
			frappe.throw(_("Required By Date is required."))

		old_doc = self.get_doc_before_save()

		# Allow an existing overdue request to be updated
		# when its required date has not been changed.
		if (
			old_doc
			and getdate(old_doc.required_by_date) == getdate(self.required_by_date)
		):
			return

		if getdate(self.required_by_date) < getdate(today()):
			frappe.throw(
				_("Required By Date cannot be in the past.")
			)
	
	def calculate_pending_quantity(self):
		requested = flt(self.requested_quantity)
		received = flt(self.received_quantity)

		self.pending_quantity = requested - received

	def calculate_expected_stock(self):
		current_stock = frappe.db.get_value(
			"Farm Inventory Balance",
			{
				"farm": self.farm,
				"inventory_item": self.inventory_item,
			},
			"current_stock",
		) or 0

		pending = flt(self.pending_quantity)

		if self.status in ("Approved", "Ordered"):
			self.expected_stock = flt(current_stock) + pending
		else:
			self.expected_stock = flt(current_stock)
