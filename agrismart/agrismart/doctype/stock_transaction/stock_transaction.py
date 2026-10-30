
import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt
from agrismart.low_stock import check_low_stock


class StockTransaction(Document):

    # begin: auto-generated types
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        amended_from: DF.Link | None
        farm: DF.Link
        inventory_item: DF.Link
        purchase_request: DF.Link | None
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

        if flt(self.quantity) <= 0:
            frappe.throw(_("Quantity must be greater than zero."))

        if self.transaction_type not in ("Stock In", "Stock Out"):
            frappe.throw(_("Invalid transaction type."))

        if self.purchase_request and self.transaction_type != "Stock In":
            frappe.throw(
                _("Purchase Request can only be linked to a Stock In transaction.")
            )

    def on_submit(self):
        self.apply_stock_movement(
            self.transaction_type,
            flt(self.quantity)
        )

        if self.transaction_type == "Stock In" and self.purchase_request:
            self.update_purchase_request_received_quantity(
                flt(self.quantity)
            )

    def on_cancel(self):
        reverse_type = (
            "Stock Out"
            if self.transaction_type == "Stock In"
            else "Stock In"
        )

        self.apply_stock_movement(
            reverse_type,
            flt(self.quantity)
        )

        if self.transaction_type == "Stock In" and self.purchase_request:
            self.update_purchase_request_received_quantity(
                -flt(self.quantity),
                is_cancellation=True
            )

    def apply_stock_movement(self, movement_type, quantity):

        # Lock Inventory Item first. This serializes stock updates
        # for the same item and protects balance creation.
        frappe.db.sql(
            """
            SELECT name
            FROM `tabInventory Item`
            WHERE name = %s
            FOR UPDATE
            """,
            (self.inventory_item,),
        )

        item = frappe.get_doc(
            "Inventory Item",
            self.inventory_item
        )

        # Find and lock the farm-specific balance.
        balance_name = frappe.db.get_value(
            "Farm Inventory Balance",
            {
                "farm": self.farm,
                "inventory_item": self.inventory_item,
            },
            "name",
        )

        if balance_name:
            frappe.db.sql(
                """
                SELECT name
                FROM `tabFarm Inventory Balance`
                WHERE name = %s
                FOR UPDATE
                """,
                (balance_name,),
            )

            balance = frappe.get_doc(
                "Farm Inventory Balance",
                balance_name
            )
        else:
            balance = frappe.get_doc({
                "doctype": "Farm Inventory Balance",
                "farm": self.farm,
                "inventory_item": self.inventory_item,
                "current_stock": 0,
            })

        farm_stock = flt(balance.current_stock)
        total_stock = flt(item.current_stock)

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
        check_low_stock(balance, item)

    def update_purchase_request_received_quantity(
        self,
        quantity_change,
        is_cancellation=False
    ):

        # Lock Purchase Request to prevent concurrent receipts.
        frappe.db.sql(
            """
            SELECT name
            FROM `tabPurchase Request`
            WHERE name = %s
            FOR UPDATE
            """,
            (self.purchase_request,),
        )

        purchase_request = frappe.get_doc(
            "Purchase Request",
            self.purchase_request
        )

        if purchase_request.farm != self.farm:
            frappe.throw(
                _("Purchase Request belongs to a different farm.")
            )

        if purchase_request.inventory_item != self.inventory_item:
            frappe.throw(
                _("Purchase Request belongs to a different inventory item.")
            )

        if not is_cancellation and purchase_request.status != "Ordered":
            frappe.throw(
                _("Only an Ordered Purchase Request can receive stock.")
            )

        current_received = flt(purchase_request.received_quantity)
        new_received = current_received + quantity_change

        if new_received < 0:
            frappe.throw(
                _("Received quantity cannot become negative.")
            )

        if new_received > flt(purchase_request.requested_quantity):
            frappe.throw(
                _("Received quantity cannot exceed requested quantity.")
            )

        purchase_request.received_quantity = new_received

        # Allow this controller to update the read-only field.
        purchase_request.flags.allow_received_quantity_update = True

        purchase_request.save(ignore_permissions=True)
        
