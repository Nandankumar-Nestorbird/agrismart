# Copyright (c) 2026, Nandan Kumar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class Farm(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		farm_name: DF.Data
		farm_owner: DF.Link
		location: DF.Data
		size_acres: DF.Float
		soil_type: DF.Literal["Clay", "Sandy", "Loamy", "Silty", "Peaty", "Chalky", "Other"]
	# end: auto-generated types

	_DOCTYPE_NAME = "Farm"

	def validate(self):
		if self.size_acres is None or self.size_acres <= 0:
			frappe.throw(_("Farm size must be greater than zero."))

		if not self.farm_owner:
			frappe.throw(_("Farm owner is required."))
