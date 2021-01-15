# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json
from frappe.model.document import Document
from frappe import _
from frappe.utils import get_url
from iyzipay_integration.utils import make_log_entry, get_iyzipay_settings
from iyzipay_integration.iyzipay_requests import get_request, post_request
from iyzipay_integration.exceptions import InvalidRequest, AuthenticationError, GatewayError

class IyzipayPayment(Document):
	def on_update(self):
		settings = get_iyzipay_settings()
		if self.status != "Authorized":
			confirm_payment(self, settings.api_key, settings.api_secret, self.flags.is_sandbox)
		set_redirect(self)

def authorise_payment():
	settings = get_iyzipay_settings()
	for doc in frappe.get_all("Iyzipay Payment", filters={"status": "Created"},
		fields=["name", "data", "reference_doctype", "reference_docname"]):

		confirm_payment(doc, settings.api_key, settings.api_secret)
		set_redirect(doc)

def confirm_payment(doc, api_key, api_secret, is_sandbox=False):
	"""
		An authorization is performed when user’s payment details are successfully authenticated by the bank.
		The money is deducted from the customer’s account, but will not be transferred to the merchant’s account
		until it is explicitly captured by merchant.
	"""
	if is_sandbox and doc.sanbox_response:
		resp = doc.sanbox_response
	else:
		resp = get_request("https://api.iyzipay.com/v1/payments/{0}".format(doc.name),
			auth=frappe._dict({"api_key": api_key, "api_secret": api_secret}))

	if resp.get("status") == "authorized":
		doc.db_set('status', 'Authorized')
		doc.run_method('on_payment_authorized')

		if doc.reference_doctype and doc.reference_docname:
			ref = frappe.get_doc(doc.reference_doctype, doc.reference_docname)
			ref.run_method('on_payment_authorized')

		doc.flags.status_changed_to = "Authorized"

def capture_payment(iyzipay_payment_id=None, is_sandbox=False, sanbox_response=None):
	"""
		Verifies the purchase as complete by the merchant.
		After capture, the amount is transferred to the merchant within T+3 days
		where T is the day on which payment is captured.

		Note: Attempting to capture a payment whose status is not authorized will produce an error.
	"""
	settings = get_iyzipay_settings()

	filters = {"status": "Authorized"}

	if is_sandbox:
		filters.update({
			"iyzipay_payment_id": iyzipay_payment_id
		})

	for doc in frappe.get_all("Iyzipay Payment", filters=filters,
		fields=["name", "data"]):

		try:
			if is_sandbox and sanbox_response:
				resp = sanbox_response

			else:
				resp = post_request("https://api.iyzipay.com/v1/payments/{0}/capture".format(doc.name),
					data={"amount": json.loads(doc.data).get("amount")},
					auth=frappe._dict({"api_key": settings.api_key, "api_secret": settings.api_secret}))

			if resp.get("status") == "captured":
				frappe.db.set_value("Iyzipay Payment", doc.name, "status", "Captured")

		except AuthenticationError as e:
			make_log_entry(e.message, json.dumps({"api_key": settings.api_key, "api_secret": settings.api_secret,
				"doc_name": doc.name, "status": doc.status}))

		except InvalidRequest as e:
			make_log_entry(e.message, json.dumps({"api_key": settings.api_key, "api_secret": settings.api_secret,
				"doc_name": doc.name, "status": doc.status}))

		except GatewayError as e:
			make_log_entry(e.message, json.dumps({"api_key": settings.api_key, "api_secret": settings.api_secret,
				"doc_name": doc.name, "status": doc.status}))

def capture_missing_payments():
	settings = get_iyzipay_settings()

	resp = get_request("https://api.iyzipay.com/v1/payments",
		auth=frappe._dict({"api_key": settings.api_key, "api_secret": settings.api_secret}))

	for payment in resp.get("items"):
		if payment.get("status") == "authorized" and not frappe.db.exists("Iyzipay Payment", payment.get("id")):
			iyzipay_payment = frappe.get_doc({
				"doctype": "Iyzipay Payment",
				"iyzipay_payment_id": payment.get("id"),
				"data": {
					"amount": payment["amount"],
					"description": payment["description"],
					"email": payment["email"],
					"contact": payment["contact"],
					"payment_request": payment["notes"]["payment_request"],
					"reference_doctype": payment["notes"]["reference_doctype"],
					"reference_docname": payment["notes"]["reference_docname"]
				},
				"status": "Authorized",
				"reference_doctype": "Payment Request",
				"reference_docname": payment["notes"]["payment_request"]
			})

			iyzipay_payment.insert(ignore_permissions=True)

def set_redirect(iyzipay_express_payment):
	"""
		ERPNext related redirects.
		You need to set Iyzipay Payment.flags.redirect_to on status change.
		Called via IyzipayPayment.on_update
	"""
	if "erpnext" not in frappe.get_installed_apps():
		return

	if not iyzipay_express_payment.flags.status_changed_to:
		return

	reference_doctype = iyzipay_express_payment.reference_doctype
	reference_docname = iyzipay_express_payment.reference_docname

	if not (reference_doctype and reference_docname):
		return

	reference_doc = frappe.get_doc(reference_doctype,  reference_docname)
	shopping_cart_settings = frappe.get_doc("Shopping Cart Settings")

	if iyzipay_express_payment.flags.status_changed_to == "Authorized":
		reference_doc.run_method("set_as_paid")

		# if shopping cart enabled and in session
		if (shopping_cart_settings.enabled
			and hasattr(frappe.local, "session")
			and frappe.local.session.user != "Guest"):

			success_url = shopping_cart_settings.payment_success_url
			if success_url:
				iyzipay_express_payment.flags.redirect_to = ({
					"Orders": "orders",
					"Invoices": "invoices",
					"My Account": "me"
				}).get(success_url, "me")
			else:
				iyzipay_express_payment.flags.redirect_to = get_url("/orders/{0}".format(reference_doc.reference_name))
