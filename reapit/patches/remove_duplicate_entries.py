import frappe

"""
Task based on:
There have been 2 transactions of the same details with 2 different vouchers. 
This has created an additional quantity without a serial number in the warehouse. 
Not sure how this happened, but it was done manually on the dashboard. Maybe connectivity issues or something like that.
"""
def execute():
    entries = ["MAT-STE-2022-338492", "MAT-STE-2023-94586"]
    for row in entries:
        frappe.db.sql(""" delete from `tabGL Entry` where voucher_no = %s """, row)
        frappe.db.sql(""" delete from `tabStock Ledger Entry` where voucher_no = %s """, row)
        frappe.db.sql(""" delete from `tabStock Entry` where name = %s """, row)
        frappe.db.sql(""" delete from `tabStock Entry Detail` where parent = %s """, row)