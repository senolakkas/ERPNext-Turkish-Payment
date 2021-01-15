# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from iyzipay_integration.utils import get_iyzipay_settings
from iyzipay_integration.iyzipay_requests import get_request
from iyzipay_integration.exceptions import AuthenticationError

class IyzipaySettings(Document):
	def validate(self):
		validate_iyzipay_credentials(iyzipay_settings=frappe._dict({
			"api_key": self.api_key,
			"api_secret": self.get_password(fieldname="api_secret")
		}))

	def on_update(self):
		create_payment_gateway_and_account()

def validate_iyzipay_credentials(doc=None, method=None, iyzipay_settings=None):
	if not iyzipay_settings:
		iyzipay_settings = get_iyzipay_settings()

	try:
		get_request(url="https://api.iyzipay.com/v1/payments", auth=frappe._dict({
			"api_key": iyzipay_settings.api_key,
			"api_secret": iyzipay_settings.api_secret
		}))
	except AuthenticationError as e:
		frappe.throw(_(e.message))

def create_payment_gateway_and_account():
	"""If ERPNext is installed, create Payment Gateway and Payment Gateway Account"""
	if "erpnext" not in frappe.get_installed_apps():
		return

	create_payment_gateway()
	create_payment_gateway_account()

def create_payment_gateway():
	# NOTE: we don't translate Payment Gateway name because it is an internal doctype
	if not frappe.db.exists("Payment Gateway", "Iyzipay"):
		payment_gateway = frappe.get_doc({
			"doctype": "Payment Gateway",
			"gateway": "Iyzipay"
		})
		payment_gateway.insert(ignore_permissions=True)

def create_payment_gateway_account():
	from erpnext.setup.setup_wizard.setup_wizard import create_bank_account

	company = frappe.db.get_value("Global Defaults", None, "default_company")
	if not company:
		return

	# NOTE: we translate Payment Gateway account name because that is going to be used by the end user
	bank_account = frappe.db.get_value("Account", {"account_name": _("Iyzipay"), "company": company},
		["name", 'account_currency'], as_dict=1)

	if not bank_account:
		# check for untranslated one
		bank_account = frappe.db.get_value("Account", {"account_name": "Iyzipay", "company": company},
			["name", 'account_currency'], as_dict=1)

	if not bank_account:
		# try creating one
		bank_account = create_bank_account({"company_name": company, "bank_account": _("Iyzipay")})

	if not bank_account:
		frappe.throw(_("Payment Gateway Account not created, please create one manually."))

	# if payment gateway account exists, return
	if frappe.db.exists("Payment Gateway Account",
		{"payment_gateway": "Iyzipay", "currency": bank_account.account_currency}):
		return

	try:
		frappe.get_doc({
			"doctype": "Payment Gateway Account",
			"is_default": 1,
			"payment_gateway": "Iyzipay",
			"payment_account": bank_account.name,
			"currency": bank_account.account_currency
		}).insert(ignore_permissions=True)

	except frappe.DuplicateEntryError:
		# already exists, due to a reinstall?
		pass
