# -*- coding: utf-8 -*-
# Copyright (c) 2021, Wahni Green Technologies and contributors
# For license information, please see license.txt
import frappe
import json
from frappe.utils.dateutils import user_to_str

@frappe.whitelist(allow_guest=True)
def used_product():
    try:
        items = json.loads(frappe.request.data)
        doc = frappe.get_doc({
            'doctype': 'Stock Entry',
            'stock_entry_type': 'Material Receipt',
            'to_warehouse': str(items['target_warehouse']),
            'items': [{
                'item_code': str(items['item_id']) + "-USED",
                'qty': 1,
                'allow_zero_valuation_rate': 1
            }]
        })
        doc.insert(ignore_permissions = True)
        doc.submit()

        doc = frappe.get_doc({
            'doctype': 'Stock Entry',
            'stock_entry_type': 'Material Issue',
            'from_warehouse': str(items['source_warehouse']),
            'items': [{
                'item_code': str(items['item_id']),
                'qty': 1,
                'allow_zero_valuation_rate': 1
            }]
        })
        doc.insert(ignore_permissions = True)
        doc.submit()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Used Product API error")
        return e
    return 0

@frappe.whitelist(allow_guest=True)
def transfer_item():
    try:
        items = json.loads(frappe.request.data)
        products = []
        for item in items['part_info']:
            products.append({
                'item_code': str(item['product_code']),
                'qty': item['product_quantity'],
                'allow_zero_valuation_rate': 1
            })
        doc = frappe.get_doc({
            'doctype': 'Stock Entry',
            'stock_entry_type': 'Material Transfer',
            'from_warehouse': str(items['source_warehouse']),
            'to_warehouse': str(items['target_warehouse']),
            'items': products
        })
        doc.insert(ignore_permissions = True)
        doc.submit()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Material Transfer API error")
        return e
    return 0

@frappe.whitelist()
def sync_item(doc, method=None):
    settings = frappe.get_single('Item Sync Settings')
    if settings.enabled:
        try:
            args = {
                "id": doc.item_code,
                "name": doc.item_name,
                "group": doc.item_group,
                "uom": doc.stock_uom,
                "hsn": doc.gst_hsn_code or "",
                "price": frappe.db.get_value('Item Price', {'price_list': settings.price_list }, 'price_list_rate') or 0.00
            }
            import requests
            api_url = settings.api_endpoint
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            if settings.auth_token:
                headers["Authorization"] = "token " + settings.auth_token
            response = requests.post(api_url, headers=headers, data=args)
            frappe.msgprint("Item synced")
        except:
            frappe.log_error(message=frappe.get_traceback(), title='Item Sync Error')
            frappe.throw("Error syncing item. Please contact system manager.")
