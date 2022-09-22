# Copyright (c) 2021, Wahni Green Technologies and contributors
# For license information, please see license.txt

import frappe
import json
from erpnext.stock.doctype.stock_reconciliation.stock_reconciliation import get_items
from frappe.utils import today, nowtime, format_date, format_time, flt, getdate
from frappe.model.mapper import get_mapped_doc
from erpnext import get_default_company
from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry


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
		frappe.db.commit()
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
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Material receipt API error")
		return e
	return 0


@frappe.whitelist(allow_guest=True)
def material_issue():
	try:
		frappe.db.commit()
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
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Material issue API error")
		return e
	return 0


@frappe.whitelist(allow_guest=True)
def used_product():
	try:
		frappe.db.commit()
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
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Used product API error")
		return e
	return 0


@frappe.whitelist(allow_guest=True)
def transfer_item():
	try:
		frappe.db.commit()
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
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Material transfer API error")
		return e
	return 0


@frappe.whitelist(allow_guest=True)
def repack_item():
	try:
		frappe.db.commit()
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
			'items': products
		})
		doc.insert(ignore_permissions=True)
		doc.submit()
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Repack API error")
		return e
	return 0


@frappe.whitelist(allow_guest=True)
def work_order():
	try:
		frappe.db.commit()
		data = json.loads(frappe.request.data)
		doc = frappe.get_doc(make_stock_entry(data.get("work_order"), "Manufacture", data.get("qty", 0)))
		doc.insert(ignore_permissions=True)
		sno_items = data.get("items")
		if sno_items:
			for item in doc.items:
				if sno_items.get(item.item_code):
					item.serial_no = "\n".join(sno_items.get(item.item_code))
		doc.submit()
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Work Order API error")
		frappe.db.rollback()
		return e
	return 0


@frappe.whitelist(allow_guest=True)
def get_sno_warehouse(sno):
	try:
		warehouse = frappe.db.get_value("Serial No", sno, "warehouse")
		if warehouse:
			return {"success": True, "warehouse": warehouse}
		return {"success": False, "warehouse": "Could not find warehouse."}
	except Exception as e:
		return {"success": False, "warehouse": str(e)}


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


@frappe.whitelist(allow_guest=True)
def add_to_transit():
	try:
		frappe.db.commit()
		data = json.loads(frappe.request.data)
		products = []
		for item in data['items']:
			products.append({
				'item_code': str(item.get('item_code')),
				'qty': item.get('qty'),
				'allow_zero_valuation_rate': 1,
				'serial_no': "\n".join(item.get('serial_no', []))
			})
		doc = frappe.get_doc({
			'doctype': 'Stock Entry',
			'stock_entry_type': 'Material Transfer',
			'add_to_transit': 1,
			'from_warehouse': str(data.get('source_warehouse')),
			'to_warehouse': str(data.get('target_warehouse')),
			'final_destination_warehouse': str(data.get('final_destination_warehouse')),
			'items': products
		})
		doc.insert(ignore_permissions=True)
		doc.submit()
		return {'success': True, 'stock_entry': doc.name}
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Transit API error")
		return {'success': False, 'error': str(e)}


@frappe.whitelist(allow_guest=True)
def end_transit():
	try:
		frappe.db.commit()
		data = json.loads(frappe.request.data)
		doc = make_stock_in_entry(data['transit_entry'], data.get('items'))
		doc.to_warehouse = frappe.db.get_value("Stock Entry", data['transit_entry'], 'final_destination_warehouse')
		doc.insert(ignore_permissions=True)
		doc.submit()
		return {'success': True, 'stock_entry': doc.name}
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "End Transit API error")
		return {'success': False, 'error': str(e)}


def make_stock_in_entry(source_name, item_dict, target_doc=None):
	def set_missing_values(source, target):
		target.set_stock_entry_type()
		target.set_missing_values()

	def update_item(source_doc, target_doc, source_parent):
		target_doc.t_warehouse = ""

		if source_doc.material_request_item and source_doc.material_request:
			add_to_transit = frappe.db.get_value("Stock Entry", source_name, "add_to_transit")
			if add_to_transit:
				warehouse = frappe.get_value(
					"Material Request Item", source_doc.material_request_item, "warehouse"
				)
				target_doc.t_warehouse = warehouse

		target_doc.s_warehouse = source_doc.t_warehouse
		target_doc.qty = item_dict[target_doc.item_code]["qty"]
		target_doc.serial_no = "\n".join(item_dict[target_doc.item_code]["serial_no"])

	doclist = get_mapped_doc(
		"Stock Entry",
		source_name,
		{
			"Stock Entry": {
				"doctype": "Stock Entry",
				"field_map": {"name": "outgoing_stock_entry"},
				"validation": {"docstatus": ["=", 1]},
			},
			"Stock Entry Detail": {
				"doctype": "Stock Entry Detail",
				"field_map": {
					"name": "ste_detail",
					"parent": "against_stock_entry",
					"serial_no": "serial_no",
					"batch_no": "batch_no",
				},
				"postprocess": update_item,
				"condition": lambda doc: (flt(doc.qty) - flt(doc.transferred_qty) > 0.01) and doc.item_code in item_dict.keys(),
			},
		},
		target_doc,
		set_missing_values,
	)

	return doclist


def attach_pdf(doc, method=None):
	if doc.purpose == "Repack":
		pdf = frappe.attach_print(
			doc.doctype,
			doc.name,
			doc=doc
		)
		frappe.get_doc({
			"doctype": "File",
			"file_name": pdf["fname"],
			"is_private": 0,
			"content": pdf["fcontent"],
			"attached_to_doctype": doc.doctype,
			"attached_to_name": doc.name
		}).save()


@frappe.whitelist()
def attach_repack_pdf(from_date, to_date):
	from_date, to_date = getdate(from_date), getdate(to_date)
	entries_to_fix = frappe.db.get_all("Stock Entry", filters={
		"docstatus": 1,
		"purpose": "Repack",
		"posting_date": ["between", [from_date, to_date]]
	}, pluck="name")
	for se in entries_to_fix:
		doc = frappe.get_doc("Stock Entry", se)
		attach_pdf(doc)
