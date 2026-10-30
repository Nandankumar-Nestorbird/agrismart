
import frappe
from frappe import _
from frappe.model.document import Document


class FarmInventoryBalance(Document):

    def validate(self):
        if not self.farm or not self.inventory_item:
            frappe.throw(_("Farm and Inventory Item are required."))

        duplicate = frappe.db.exists(
            "Farm Inventory Balance",
            {
                "farm": self.farm,
                "inventory_item": self.inventory_item,
                "name": ["!=", self.name]
            }
        )

        if duplicate:
            frappe.throw(
                _("A Farm Inventory Balance already exists for this Farm and Inventory Item.")
            )

        if self.current_stock is None or self.current_stock < 0:
            frappe.throw(_("Current Stock cannot be negative."))
