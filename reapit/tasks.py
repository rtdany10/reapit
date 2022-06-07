# Copyright (c) 2021, Wahni Green Technologies and contributors
# For license information, please see license.txt
import frappe
import json
from erpnext.stock.doctype.stock_reconciliation.stock_reconciliation import get_items
from frappe.utils.data import today, nowtime, format_date, format_time
from erpnext import get_default_company


@frappe.whitelist(allow_guest=True)
def check_item(item_id):
	try:
		value = frappe.db.get_value('Item', str(item_id), 'disabled')
		if value in [0, 1]:
			return {'exists': 1, 'enabled': not value}
		return {'exists': 0, 'enabled': value}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Item check API error")
		return e


@frappe.whitelist(allow_guest=True)
def warehouse_stock():
	try:
		items = json.loads(frappe.request.data)
		if not items.get('date'):
			items['date'] = today()
		else:
			items['date'] = format_date(items['date'])
		if not items.get('time'):
			items['time'] = nowtime()
		else:
			items['time'] = format_time(items['time'])
		if not items.get('company'):
			items['company'] = get_default_company()
		return get_items(str(items['warehouse']), items['date'], items['time'], items['company'], items.get('item_code'))
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Warehouse stock API error")
		return e


@frappe.whitelist(allow_guest=True)
def material_receipt():
	try:
		items = json.loads(frappe.request.data)
		doc = frappe.get_doc({
			'doctype': 'Stock Entry',
			'stock_entry_type': 'Material Receipt',
			'to_warehouse': str(items.get('target_warehouse')),
			'items': [{
				'item_code': str(items.get('item_id')),
				'qty': items.get('product_quantity'),
				'allow_zero_valuation_rate': 1,
				'serial_no': "\n".join(items.get('serial_no', []))
			}]
		})
		doc.insert(ignore_permissions=True)
		doc.submit()
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Material receipt API error")
		return e
	return 0


@frappe.whitelist(allow_guest=True)
def material_issue():
	try:
		items = json.loads(frappe.request.data)
		doc = frappe.get_doc({
			'doctype': 'Stock Entry',
			'stock_entry_type': 'Material Issue',
			'from_warehouse': str(items.get('source_warehouse')),
			'items': [{
				'item_code': str(items.get('item_id')),
				'qty': items.get('product_quantity'),
				'allow_zero_valuation_rate': 1,
				'serial_no': "\n".join(items.get('serial_no', []))
			}]
		})
		doc.insert(ignore_permissions=True)
		doc.submit()
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Material issue API error")
		return e
	return 0


@frappe.whitelist(allow_guest=True)
def used_product():
	try:
		items = json.loads(frappe.request.data)
		doc = frappe.get_doc({
			'doctype': 'Stock Entry',
			'stock_entry_type': 'Material Receipt',
			'to_warehouse': str(items.get('target_warehouse')),
			'items': [{
				'item_code': str(items.get('item_id')) + "-USED",
				'qty': 1,
				'allow_zero_valuation_rate': 1
			}]
		})
		doc.insert(ignore_permissions=True)
		doc.submit()

		doc = frappe.get_doc({
			'doctype': 'Stock Entry',
			'stock_entry_type': 'Material Issue',
			'from_warehouse': str(items.get('source_warehouse')),
			'items': [{
				'item_code': str(items.get('item_id')),
				'qty': 1,
				'allow_zero_valuation_rate': 1
			}]
		})
		doc.insert(ignore_permissions=True)
		doc.submit()
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Used product API error")
		return e
	return 0


@frappe.whitelist(allow_guest=True)
def transfer_item():
	try:
		items = json.loads(frappe.request.data)
		products = []
		for item in items['part_info']:
			products.append({
				'item_code': str(item.get('product_code')),
				'qty': item.get('product_quantity'),
				'set_basic_rate_manually': item.get('zero_rate', 0),
				'allow_zero_valuation_rate': 1,
				'serial_no': "\n".join(item.get('serial_no', []))
			})
		doc = frappe.get_doc({
			'doctype': 'Stock Entry',
			'stock_entry_type': 'Material Transfer',
			'from_warehouse': str(items.get('source_warehouse')),
			'to_warehouse': str(items.get('target_warehouse')),
			'items': products
		})
		doc.insert(ignore_permissions=True)
		doc.submit()
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Material transfer API error")
		return e
	return 0


@frappe.whitelist(allow_guest=True)
def repack_item():
	try:
		items = json.loads(frappe.request.data)
		products = [{
			's_warehouse': items.get('source_warehouse'),
			'item_code': str(items.get('repack_item')),
			'qty': items.get('repack_qty'),
			'allow_zero_valuation_rate': 1,
			'serial_no': "\n".join(items.get('serial_no', []))
		}]
		for item in items['target_items']:
			products.append({
				't_warehouse': items.get('target_warehouse'),
				'item_code': str(item.get('product_code')),
				'qty': item.get('product_quantity'),
				'set_basic_rate_manually': item.get('zero_rate', 0),
				'allow_zero_valuation_rate': 1,
				'serial_no': "\n".join(item.get('serial_no', []))
			})
		doc = frappe.get_doc({
			'doctype': 'Stock Entry',
			'stock_entry_type': 'Repack',
			'items': products
		})
		doc.insert(ignore_permissions=True)
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Repack API error")
		return e
	return 0


@frappe.whitelist(allow_guest=True)
def submit_repack():
	try:
		frappe.db.commit()
		data = json.loads(frappe.request.data)
		doc = frappe.get_doc("Stock Entry", data.get("repack_entry"))
		doc.run_method('submit')
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Repack API error")
		frappe.db.rollback()
		return e
	return 0


@frappe.whitelist(allow_guest=True)
def work_order():
	try:
		data = json.loads(frappe.request.data)
		doc = frappe.get_doc({
			'doctype': 'Work Order',
			'stock_entry_type': 'Repack',
			'production_item': data.get("production_item"),
			'bom_no': data.get("bom_no"),
			'qty': data.get("qty"),
			'wip_warehouse': data.get("wip_warehouse"),
			'fg_warehouse': data.get("fg_warehouse")
		})
		doc.insert(ignore_permissions=True)
		doc.submit()
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Repack API error")
		return e
	return 0


@frappe.whitelist()
def sync_item(doc, method=None):
	settings = frappe.get_single('Item Sync Settings')
	action = "delete" if method == "on_trash" else "edit"
	action = "add" if doc.is_new() else action
	if settings.enabled:
		try:
			args = json.dumps({
				"id": doc.item_code,
				"name": doc.item_name,
				"group": doc.item_group,
				"uom": doc.stock_uom,
				"hsn": doc.gst_hsn_code or "",
				"price": frappe.db.get_value('Item Price', {'price_list': settings.price_list}, 'price_list_rate') or 0.00,
				"type": doc.item_type,
				"serialized": 1 if doc.serialized == "Yes" else 0,
				"disabled": doc.disabled,
				"action": action
			})
			import requests
			api_url = settings.api_endpoint
			headers = {
				"Accept": "application/json",
				"Content-Type": "application/json"
			}
			if settings.auth_token:
				headers["Authorization"] = "Bearer " + settings.auth_token
			response = requests.post(api_url, headers=headers, data=args)
			if response.status_code == 200:
				frappe.msgprint("Item synced")
			else:
				frappe.msgprint("Error syncing: " + str(response.text))
		except Exception:
			frappe.log_error(message=frappe.get_traceback(), title='Item Sync Error')
			frappe.throw("Error syncing item. Please contact system manager.")
