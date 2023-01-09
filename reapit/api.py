# Copyright (c) 2021, Wahni IT Solutions and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.integrations.utils import create_request_log


@frappe.whitelist()
def repack_item_draft():
	try:
		data = json.loads(frappe.request.data)
		products = []
		for item in data['items']:
			products.append({
				's_warehouse': item.get('source_warehouse'),
				't_warehouse': item.get('target_warehouse'),
				'item_code': str(item.get('product_code')),
				'qty': item.get('product_quantity'),
				'set_basic_rate_manually': item.get('zero_rate', 0),
				'allow_zero_valuation_rate': 1,
				'serial_no': "\n".join(item.get('serial_no', []))
			})
		doc = frappe.get_doc({
			'doctype': 'Stock Entry',
			'stock_entry_type': 'Repack',
			'items': products,
			'old_bot_id': data.get("old_bot_id"),
			'new_bot_id': data.get("new_bot_id"),
			'sponsor_id': data.get("sponsor_id"),
			'old_purifier_id': data.get("old_purifier_id"),
			'new_purifier_id': data.get("new_purifier_id"),
			'refurbishment_category': data.get("refurbishment_category")
		})
		doc.insert(ignore_permissions=True)
		return {
			"success": True,
			"message": "Repack Entry Created.",
			"id": doc.name
		}
	except Exception as e:
		frappe.db.rollback()
		create_request_log(
			data=json.loads(frappe.request.data),
			request_description = "Repack API Draft",
			service_name="Reapit",
			request_headers=frappe.request.headers,
			error=str(e),
			status="Failed"
		)
		return {"success": False, "error": str(e)}