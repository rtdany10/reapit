import frappe

def execute():
	entries_to_fix = frappe.db.get_all("Stock Entry", filters={
		"docstatus": 1,
		"purpose": "Repack"
	}, pluck="name")
	for se in entries_to_fix:
		doc = frappe.get_doc("Stock Entry", se)
		rf_cost = 0.0
		for row in doc.items:
			if row.item_code != '2001' and not row.t_warehouse:
				rf_cost += row.basic_amount
		doc.db_set("refurbishment_cost", rf_cost)
				
