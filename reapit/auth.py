# Copyright (c) 2021, Wahni IT Solutions and contributors
# For license information, please see license.txt

import base64
import json

import frappe
from frappe.utils.password import get_decrypted_password


@frappe.whitelist(allow_guest=True)
def authenticate():
	try:
		data = json.loads(frappe.request.data)
		username = data.get("username")
		password = data.get("password")
		try:
			login_manager = frappe.auth.LoginManager()
			login_manager.authenticate(user=username, pwd=password)
		except Exception:
			frappe.local.response["status_code"] = 400
			return {"success": False, "message": "Invalid username or password"}

		login_manager.post_login()
		token = generate_keys(username)

		return {
			"success": True,
			"message": "Logged In Succesfully",
			"token": token
		}
	except Exception as e:
		frappe.log_error(str(e), "Auth Error")
		return {"success": False, "error": str(e)}


def generate_keys(user):
	api_secret = get_decrypted_password("User", user, "api_secret", raise_exception=False)
	if not api_secret:
		user_details = frappe.get_doc("User", user)
		api_secret = frappe.generate_hash(length=15)
		# if api key is not set generate api key
		if not user_details.api_key:
			api_key = frappe.generate_hash(length=15)
			user_details.api_key = api_key
		user_details.api_secret = api_secret
		user_details.save()
	else:
		api_key = frappe.db.get_value("User", user, "api_key")

	return base64.b64encode(('{}:{}'.format(api_key, api_secret)).encode('utf-8')).decode('utf-8')