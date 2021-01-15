# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest
import json
from iyzipay_integration.exceptions import InvalidRequest, AuthenticationError
from iyzipay_integration.iyzipay_integration.doctype.iyzipay_payment.iyzipay_payment import capture_payment

data = {
	"iyzipay_settings": {
		"api_key": "rzp_test_lExD7NVL1JoKJJ",
		"api_secret": "ceM6bQs4vWgV30QcEu6yVil"
	},
	"options": {
		"key": "rzp_test_lExD7NVL1JoKJJ",
		"amount": 2000,
		"name": "_Test Company 1",
		"description": "Test Payment Request",
		"image": "./assets/erpnext/images/erp-icon.svg",
		"prefill": {
			"name": "_Test Customer 1",
			"email": "test@erpnext.com",
		},
		"theme": {
			"color": "#4B4C9D"
		}
	},
	"sanbox_response": {
		"entity": "payment",
		"amount": 500,
		"currency": "INR",
		"amount_refunded": 0,
		"refund_status": None,
		"email": "test@iyzipay.com",
		"contact": "9364591752",
		"error_code": None,
		"error_description": None,
		"notes": {},
		"created_at": 1400826750
	}
}

class TestIyzipayPayment(unittest.TestCase):
	def test_iyzipay_settings(self):
		iyzipay_settings = frappe.get_doc("Iyzipay Settings")
		iyzipay_settings.update(data["iyzipay_settings"])
		
		self.assertRaises(AuthenticationError, iyzipay_settings.insert)
	
	def test_confirm_payment(self):
		iyzipay_payment_id = "test_pay_{0}".format(frappe.generate_hash(length=14))
		iyzipay_payment = make_payment(iyzipay_payment_id=iyzipay_payment_id,
			options=json.dumps(data["options"]))
			
		self.assertRaises(InvalidRequest, iyzipay_payment.insert)
		
		iyzipay_settings = frappe.get_doc("Iyzipay Settings")
		iyzipay_settings.update(data["iyzipay_settings"])
		
		iyzipay_payment_id = "test_pay_{0}".format(frappe.generate_hash(length=14))
		
		iyzipay_payment = make_payment(iyzipay_payment_id=iyzipay_payment_id,
			options=json.dumps(data["options"]))
			
		iyzipay_payment.flags.is_sandbox = True
		iyzipay_payment.sanbox_response = data["sanbox_response"]
		iyzipay_payment.sanbox_response.update({
			"id": iyzipay_payment_id,
			"status": "authorized"
		})
		
		iyzipay_payment.insert(ignore_permissions=True)
		
		iyzipay_payment_status = frappe.db.get_value("Iyzipay Payment", iyzipay_payment_id, "status")
		
		self.assertEquals(iyzipay_payment_status, "Authorized")
		
	def test_capture_payment(self):
		iyzipay_settings = frappe.get_doc("Iyzipay Settings")
		iyzipay_settings.update(data["iyzipay_settings"])
		
		iyzipay_payment_id = "test_pay_{0}".format(frappe.generate_hash(length=14))
		
		iyzipay_payment = make_payment(iyzipay_payment_id=iyzipay_payment_id,
			options=json.dumps(data["options"]))
			
		iyzipay_payment.flags.is_sandbox = True
		iyzipay_payment.sanbox_response = data["sanbox_response"]
		iyzipay_payment.sanbox_response.update({
			"id": iyzipay_payment_id,
			"status": "authorized"
		})
		
		iyzipay_payment.insert(ignore_permissions=True)
		
		iyzipay_payment.sanbox_response.update({
			"id": iyzipay_payment_id,
			"status": "captured"
		})
		
		capture_payment(iyzipay_payment_id=iyzipay_payment_id ,is_sandbox=True,
			sanbox_response=iyzipay_payment.sanbox_response)
		
		iyzipay_payment_status = frappe.db.get_value("Iyzipay Payment", iyzipay_payment_id, "status")
		
		self.assertEquals(iyzipay_payment_status, "Captured")
		
def make_payment(**args):
	args = frappe._dict(args)
	
	iyzipay_payment = frappe.get_doc({
		"doctype": "Iyzipay Payment",
		"iyzipay_payment_id": args.iyzipay_payment_id,
		"data": args.options
	})
	
	return iyzipay_payment
	