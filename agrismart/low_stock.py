
import frappe
from frappe import _
from frappe.utils import flt, today, add_days


def check_low_stock(balance, item):
    """
    Check farm-wise stock against the Inventory Item reorder level.
    Notify Farm Owner and Delivery Manager when stock is low.
    """

    current_stock = frappe.utils.flt(balance.current_stock)
    reorder_level = frappe.utils.flt(item.reorder_level)

    # Stock has recovered: allow a future low-stock alert.
    if current_stock > reorder_level:
        if balance.low_stock_notified:
            balance.low_stock_notified = 0
            balance.save(ignore_permissions=True)
        return
    # Automatically generate Purchase Request.
    generate_purchase_request(balance, item)
    # Prevent duplicate notifications while stock remains low.
    if balance.low_stock_notified:
        return

    # Get Farm Owner.
    farm_owner = frappe.db.get_value(
        "Farm",
        balance.farm,
        "farm_owner"
    )

    recipients = set()

    if farm_owner and farm_owner not in ("Guest",):
        recipients.add(farm_owner)

    # Get all enabled users with Delivery Manager role.
    delivery_manager_users = frappe.get_all(
        "Has Role",
        filters={"role": "Delivery Manager"},
        pluck="parent"
    )

    if delivery_manager_users:
        active_users = frappe.get_all(
            "User",
            filters={
                "name": ["in", list(delivery_manager_users)],
                "enabled": 1
            },
            pluck="name"
        )
        recipients.update(active_users)

    recipients.discard("Guest")

    # Do not mark the alert as sent if no recipients are configured.
    if not recipients:
        frappe.log_error(
            "No active Farm Owner or Delivery Manager found for "
            f"Farm Inventory Balance {balance.name}",
            "Agrismart Low Stock Notification"
        )
        return

    farm_name = frappe.db.get_value(
        "Farm", balance.farm, "farm_name"
    )

    subject = _("Low Stock Alert: {0}").format(item.item_name)

    message = _(
        "Low stock alert for Farm: {0}<br>"
        "Inventory Item: {1}<br>"
        "Current Stock: {2}<br>"
        "Reorder Level: {3}<br><br>"
        "Please review the inventory and create a Purchase Request if required."
    ).format(
        farm_name or balance.farm,
        item.item_name,
        current_stock,
        reorder_level
    )

    # Create an in-app Notification Log for each recipient.
    for user in recipients:
        frappe.get_doc({
            "doctype": "Notification Log",
            "subject": subject,
            "email_content": message,
            "for_user": user,
            "type": "Alert",
            "document_type": "Farm Inventory Balance",
            "document_name": balance.name
        }).insert(ignore_permissions=True)

    # Resolve email addresses for enabled users.
    user_emails = frappe.get_all(
        "User",
        filters={
            "name": ["in", list(recipients)],
            "enabled": 1
        },
        fields=["name", "email"]
    )

    email_recipients = list({
        user.email or user.name
        for user in user_emails
        if user.email or user.name
    })

    # Send one email to all recipients.
    if email_recipients:
        frappe.sendmail(
            recipients=email_recipients,
            subject=subject,
            message=message,
            reference_doctype="Farm Inventory Balance",
            reference_name=balance.name
        )

    # Mark alert as sent to avoid duplicate notifications.
    balance.low_stock_notified = 1
    balance.save(ignore_permissions=True)


def generate_purchase_request(balance, item):
    """
    Automatically create a Draft Purchase Request
    when farm inventory reaches its reorder level.
    """

    current_stock = flt(balance.current_stock)
    reorder_level = flt(item.reorder_level)
    target_stock = flt(item.custom_target_stock_level)

    # Generate PR only when stock is at or below reorder level.
    if current_stock > reorder_level:
        return None

    # Target stock must be configured.
    if target_stock <= reorder_level:
        frappe.log_error(
            f"Invalid Target Stock Level for Inventory Item {item.name}",
            "Agrismart Automatic Purchase Request"
        )
        return None

    # Check whether a Draft PR already exists.
    existing_draft = frappe.db.exists(
        "Purchase Request",
        {
            "farm": balance.farm,
            "inventory_item": item.name,
            "status": "Draft"
        }
    )

    if existing_draft:
        return existing_draft

    # Calculate pending quantity from Approved and Ordered requests.
    active_requests = frappe.get_all(
        "Purchase Request",
        filters={
            "farm": balance.farm,
            "inventory_item": item.name,
            "status": ["in", ["Approved", "Ordered"]]
        },
        fields=["pending_quantity"]
    )

    existing_pending_quantity = sum(
        flt(request.pending_quantity)
        for request in active_requests
    )

    # Calculate suggested purchase quantity.
    suggested_quantity = (
        target_stock
        - current_stock
        - existing_pending_quantity
    )

    if suggested_quantity <= 0:
        return None

    # Create a Draft Purchase Request.
    purchase_request = frappe.get_doc({
        "doctype": "Purchase Request",
        "farm": balance.farm,
        "inventory_item": item.name,
        "requested_quantity": suggested_quantity,
        "received_quantity": 0,
        "required_by_date": add_days(today(), 7),
        "status": "Draft"
    })

    purchase_request.insert(ignore_permissions=True)

    frappe.logger("agrismart").info(
        f"Automatic Purchase Request created: {purchase_request.name}"
    )

    return purchase_request.name
