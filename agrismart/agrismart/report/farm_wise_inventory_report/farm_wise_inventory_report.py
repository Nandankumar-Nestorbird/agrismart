# Copyright (c) 2026, Nandan Kumar and contributors
# For license information, please see license.txt

from frappe import _
import frappe

def execute(filters=None):
    columns = [
        {
            "label": "Farm Name",
            "fieldname": "farm",
            "fieldtype": "Link",
            "options": "Farm",
            "width": 180,
        },
        {
            "label": "Inventory Item",
            "fieldname": "inventory_item",
            "fieldtype": "Link",
            "options": "Inventory Item",
            "width": 180,
        },
        {
            "label": "Current Stock",
            "fieldname": "current_stock",
            "fieldtype": "Float",
            "width": 120,
        },
        {
            "label": "Reorder Level",
            "fieldname": "reorder_level",
            "fieldtype": "Float",
            "width": 120,
        },
        {
            "label": "Stock Status",
            "fieldname": "stock_status",
            "fieldtype": "Data",
            "width": 140,
        },
    ]
    data = frappe.db.sql(
        """
        SELECT
            b.farm,
            b.inventory_item,
            b.current_stock,
            i.reorder_level,
            CASE
                WHEN b.current_stock <= i.reorder_level
                THEN 'Low Stock'
                ELSE 'Available'
            END AS stock_status
        FROM `tabFarm Inventory Balance` b
        INNER JOIN `tabInventory Item` i
            ON i.name = b.inventory_item
        ORDER BY b.farm, i.item_name
        """,
        as_dict=True,
    )
    return columns, data

def execute_snapshot_report(filters: dict | None = None):
	"""Return columns and data for the report.

	This is the main entry point for snapshot report. When 'Synced
	Report' is enabled in report, framework will call this method
	every time the report is refreshed or a filter is updated. It
	accepts the same filters as normal execute. But a utility method -
	get_latest_sync, is also imported.

	"""
	from frappe.database.duckdb.database import get_latest_sync

	columns = get_columns()
	data = get_data()

	return columns, data

def get_columns() -> list[dict]:
	"""Return columns for the report.

	One field definition per column, just like a DocType field definition.
	"""
	return [
		{
			"label": _("Column 1"),
			"fieldname": "column_1",
			"fieldtype": "Data",
		},
		{
			"label": _("Column 2"),
			"fieldname": "column_2",
			"fieldtype": "Int",
		},
	]


def get_data() -> list[list]:
	"""Return data for the report.

	The report data is a list of rows, with each row being a list of cell values.
	"""
	return [
		["Row 1", 1],
		["Row 2", 2],
	]
