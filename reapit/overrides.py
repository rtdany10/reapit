# Copyright (c) 2022, Wahni Green Technologies and contributors
# For license information, please see license.txt

from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry
from erpnext.stock.utils import get_incoming_rate
from frappe.utils import flt


class CustomStockEntry(StockEntry):
	def set_rate_for_outgoing_items(self, reset_outgoing_rate=True, raise_error_if_no_rate=True):
		outgoing_items_cost = 0.0
		for d in self.get("items"):
			if d.s_warehouse:
				if not d.set_basic_rate_manually and reset_outgoing_rate:
					args = self.get_args_for_incoming_rate(d)
					rate = get_incoming_rate(args, raise_error_if_no_rate)
					if rate > 0:
						d.basic_rate = rate

				d.basic_amount = flt(flt(d.transfer_qty) * flt(d.basic_rate), d.precision("basic_amount"))
				if not d.t_warehouse:
					outgoing_items_cost += flt(d.basic_amount)

		return outgoing_items_cost
