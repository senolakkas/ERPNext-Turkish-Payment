# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import get_url, flt
from iyzipay_integration.utils import make_log_entry, validate_transaction_currency, get_iyzipay_settings
from iyzipay_integration.exceptions import InvalidRequest, AuthenticationError, GatewayError
import urllib

no_cache = 1
no_sitemap = 1

expected_keys = ('amount', 'title', 'description', 'doctype', 'name',
	'payer_name', 'payer_email', 'order_id')

def get_context(context):
	context.no_cache = 1
	context.api_key = get_iyzipay_settings().api_key

	context.brand_image = (frappe.db.get_value("Iyzipay Settings", None, "brand_image")
		or './assets/erpnext/images/erp-icon.svg')

	if frappe.form_dict.payment_request:
		payment_req = frappe.get_doc('Payment Request', frappe.form_dict.payment_request)
		validate_transaction_currency(payment_req.currency)

		if payment_req.status == "Paid":
			frappe.redirect_to_message(_('Already Paid'), _('You have already paid for this order'))
			return

		reference_doc = frappe.get_doc(payment_req.reference_doctype, payment_req.reference_name)

		context.amount = payment_req.grand_total
		context.title = reference_doc.company
		context.description = payment_req.subject
		context.doctype = payment_req.doctype
		context.name = payment_req.name
		context.payer_name = reference_doc.customer_name
		context.payer_email = reference_doc.get('email_to') or frappe.session.user
		context.order_id = payment_req.name
		context.reference_doctype = payment_req.reference_doctype
		context.reference_name = payment_req.reference_name

	# all these keys exist in form_dict
	elif not (set(expected_keys) - set(frappe.form_dict.keys())):
		for key in expected_keys:
			context[key] = frappe.form_dict[key]

		context['amount'] = flt(context['amount'])
		context['reference_doctype'] = context['reference_name'] = None

	else:
		frappe.redirect_to_message(_('Some information is missing'), _('Looks like someone sent you to an incomplete URL. Please ask them to look into it.'))
		frappe.local.flags.redirect_location = frappe.local.response.location
		raise frappe.Redirect

def get_checkout_url(**kwargs):
	missing_keys = set(expected_keys) - set(kwargs.keys())
	if missing_keys:
		frappe.throw(_('Missing keys to build checkout URL: {0}').format(", ".join(list(missing_keys))))

	return get_url('/iyzipay_checkout?{0}'.format(urllib.urlencode(kwargs)))

@frappe.whitelist(allow_guest=True)
def make_payment(iyzipay_payment_id, options, reference_doctype, reference_docname):
	try:
		iyzipay_payment = frappe.get_doc({
			"doctype": "Iyzipay Payment",
			"iyzipay_payment_id": iyzipay_payment_id,
			"data": options,
			"reference_doctype": reference_doctype,
			"reference_docname": reference_docname
		})

		iyzipay_payment.insert(ignore_permissions=True)

		if frappe.db.get_value("Iyzipay Payment", iyzipay_payment.name, "status") == "Authorized":
			return {
				"redirect_to": iyzipay_payment.flags.redirect_to or "iyzipay-payment-success",
				"status": 200
			}

	except AuthenticationError as e:
		make_log_entry(e.message, options)
		return{
			"redirect_to": frappe.redirect_to_message(_('Server Error'), _("Seems issue with server's iyzipay config. Don't worry, in case of failure amount will get refunded to your account.")),
			"status": 401
		}

	except InvalidRequest as e:
		make_log_entry(e.message, options)
		return {
			"redirect_to": frappe.redirect_to_message(_('Server Error'), _("Seems issue with server's iyzipay config. Don't worry, in case of failure amount will get refunded to your account.")),
			"status": 400
		}

	except GatewayError as e:
		make_log_entry(e.message, options)
		return {
			"redirect_to": frappe.redirect_to_message(_('Server Error'), _("Seems issue with server's iyzipay config. Don't worry, in case of failure amount will get refunded to your account.")),
			"status": 500
		}
