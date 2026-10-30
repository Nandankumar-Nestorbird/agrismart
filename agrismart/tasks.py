
import frappe
from frappe import _
from frappe.utils import getdate, today, flt


def send_purchase_request_reminders():
    """Send daily reminders for overdue or due ordered requests."""

    requests = frappe.get_all(
        "Purchase Request",
        filters={
            "status": "Ordered",
            "required_by_date": ["<=", today()],
            "pending_quantity": [">", 0],
        },
        fields=[
            "name",
            "farm",
            "inventory_item",
            "requested_quantity",
            "received_quantity",
            "pending_quantity",
            "required_by_date",
            "last_reminder_date",
        ],
    )

    for request in requests:
        if request.last_reminder_date == getdate(today()):
            continue

        farm = frappe.db.get_value(
            "Farm",
            request.farm,
            ["farm_name", "farm_owner"],
            as_dict=True,
        )

        item_name = frappe.db.get_value(
            "Inventory Item",
            request.inventory_item,
            "item_name",
        )

        recipients = set()

        if farm and farm.farm_owner:
            recipients.add(farm.farm_owner)

        delivery_managers = frappe.get_all(
            "Has Role",
            filters={"role": "Delivery Manager"},
            pluck="parent",
        )

        if delivery_managers:
            active_users = frappe.get_all(
                "User",
                filters={
                    "name": ["in", delivery_managers],
                    "enabled": 1,
                },
                pluck="name",
            )
            recipients.update(active_users)

        recipients.discard("Guest")

        if not recipients:
            continue

        subject = _("Purchase Request Reminder: {0}").format(
            request.name
        )

        message = _(
            "A Purchase Request requires your attention.<br><br>"
            "Purchase Request: {0}<br>"
            "Farm: {1}<br>"
            "Inventory Item: {2}<br>"
            "Requested Quantity: {3}<br>"
            "Received Quantity: {4}<br>"
            "Pending Quantity: {5}<br>"
            "Required By Date: {6}"
        ).format(
            request.name,
            farm.farm_name if farm else request.farm,
            item_name or request.inventory_item,
            request.requested_quantity,
            request.received_quantity,
            request.pending_quantity,
            request.required_by_date,
        )

        for user in recipients:
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": subject,
                "email_content": message,
                "for_user": user,
                "type": "Alert",
                "document_type": "Purchase Request",
                "document_name": request.name,
            }).insert(ignore_permissions=True)

        users = frappe.get_all(
            "User",
            filters={
                "name": ["in", list(recipients)],
                "enabled": 1,
            },
            fields=["name", "email"],
        )

        emails = list({
            user.email or user.name
            for user in users
            if user.email or user.name
        })

        if emails:
            frappe.sendmail(
                recipients=emails,
                subject=subject,
                message=message,
                reference_doctype="Purchase Request",
                reference_name=request.name,
            )

        frappe.db.set_value(
            "Purchase Request",
            request.name,
            "last_reminder_date",
            today(),
            update_modified=False,
        )
