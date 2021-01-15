// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Iyzipay Settings', {
	refresh: function(frm) {
		frm.add_custom_button(__("Iyzipay Logs"), function() {
			frappe.set_route("List", "Iyzipay Log");
		})
		frm.add_custom_button(__("Payment Logs"), function() {
			frappe.set_route("List", "Iyzipay Payment");
		});
		frm.add_custom_button(__("Payment Gateway Accounts"), function() {
			frappe.route_options = {"payment_gateway": "Iyzipay"};
			frappe.set_route("List", "Payment Gateway Account");
		});
	}
});
