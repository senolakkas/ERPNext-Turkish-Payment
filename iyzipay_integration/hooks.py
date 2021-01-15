# -*- coding: utf-8 -*-
from __future__ import unicode_literals

app_name = "iyzipay_integration"
app_title = "Iyzipay Integration"
app_publisher = "Frappe Technologies Pvt. Ltd."
app_description = "Iyzipay Payment Gateway Integration"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "info@frappe.io"
app_version = "0.0.1"
app_license = "MIT"
hide_in_installer = True
# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/iyzipay_integration/css/iyzipay_integration.css"
# app_include_js = "/assets/iyzipay_integration/js/iyzipay_integration.js"

# include js, css files in header of web template
# web_include_css = "/assets/iyzipay_integration/css/iyzipay_integration.css"
# web_include_js = "/assets/iyzipay_integration/js/iyzipay_integration.js"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "iyzipay_integration.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "iyzipay_integration.install.before_install"
# after_install = "iyzipay_integration.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "iyzipay_integration.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Payment Request": {
		"validate": "iyzipay_integration.iyzipay_integration.doctype.iyzipay_settings.iyzipay_settings.validate_iyzipay_credentials",
		"get_payment_url": "iyzipay_integration.utils.get_payment_url"
	},
	"Shopping Cart Settings": {
		"validate": "iyzipay_integration.utils.validate_price_list_currency"
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"all": [
		"iyzipay_integration.iyzipay_integration.doctype.iyzipay_payment.iyzipay_payment.authorise_payment",
		"iyzipay_integration.iyzipay_integration.doctype.iyzipay_payment.iyzipay_payment.capture_payment"
	]
}

# Testing
# -------

# before_tests = "iyzipay_integration.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "iyzipay_integration.event.get_events"
# }

