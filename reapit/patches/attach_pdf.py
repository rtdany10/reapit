import frappe
from reapit.tasks import attach_pdf

def execute():
	entries_to_fix = frappe.db.get_all("Stock Entry", filters={
		"docstatus": 1,
		"purpose": "Repack",
		"posting_date": [">=", "01-07-2022"]
	}, pluck="name")
	for se in entries_to_fix:
		doc = frappe.get_doc("Stock Entry", se)
		attach_pdf(doc)
