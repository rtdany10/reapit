# -*- coding: utf-8 -*-
# Copyright (c) 2021, Wahni Green Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe.model.document import Document


class ItemSyncSettings(Document):
	def validate(self):
		if self.enabled:
			if not (self.api_endpoint and self.price_list):
				frappe.throw("Invalid endpoint or price list.")
