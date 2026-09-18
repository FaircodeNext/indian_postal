# Copyright (c) 2026, FaircodeNext Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from indian_postal.api.postal import validate_pincode


class IndianPostalCode(Document):
	def before_insert(self):
		# Runs before the "format:{pincode}-{post_office_name}" autoname is applied,
		# so the docname is built from cleaned values rather than raw user input.
		self._normalize()

	def validate(self):
		self._normalize()

	def _normalize(self):
		self.pincode = validate_pincode(self.pincode)
		self.post_office_name = (self.post_office_name or "").strip()
		if not self.post_office_name:
			frappe.throw(frappe._("Post Office Name is required."))

	@frappe.whitelist()
	def fetch_latest_data(self):
		"""Refresh this record (and any sibling Post Offices for the same pincode)
		from the external PostalPincode API, called by the 'Fetch Latest Data' button."""
		from indian_postal.api.postal import get_postal_details

		return get_postal_details(self.pincode, force_refresh=1)
