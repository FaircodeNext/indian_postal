# Copyright (c) 2026, FaircodeNext Technologies and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

TEST_PINCODE = "683513"
TEST_POST_OFFICE = "Ezhikkara"
TEST_NAME = f"{TEST_PINCODE}-{TEST_POST_OFFICE}"


class TestIndianPostalCode(IntegrationTestCase):
	def tearDown(self):
		frappe.db.delete("Indian Postal Code", {"pincode": TEST_PINCODE})

	def _make(self, post_office_name=TEST_POST_OFFICE, **kwargs):
		doc = frappe.get_doc(
			{
				"doctype": "Indian Postal Code",
				"pincode": TEST_PINCODE,
				"post_office_name": post_office_name,
				"branch_type": "Branch Post Office",
				"delivery_status": "Delivery",
				"circle": "Kerala",
				"district": "Ernakulam",
				"division": "Alwaye",
				"region": "Kochi",
				"block": "Paravur",
				"state": "Kerala",
				"country": "India",
				**kwargs,
			}
		)
		doc.insert()
		return doc

	def test_autoname_combines_pincode_and_post_office(self):
		doc = self._make()
		self.assertEqual(doc.name, TEST_NAME)

	def test_pincode_alone_is_not_unique(self):
		self._make(post_office_name="Ezhikkara")
		second = self._make(post_office_name="Paravur")
		self.assertEqual(second.pincode, TEST_PINCODE)
		self.assertNotEqual(second.name, TEST_NAME)

	def test_duplicate_pincode_and_post_office_is_rejected(self):
		self._make()
		with self.assertRaises(frappe.DuplicateEntryError):
			self._make()

	def test_invalid_pincode_is_rejected_on_save(self):
		with self.assertRaises(frappe.ValidationError):
			self._make(pincode="68351")

	def test_pincode_whitespace_is_stripped(self):
		doc = self._make(pincode=f" {TEST_PINCODE} ")
		self.assertEqual(doc.pincode, TEST_PINCODE)
		self.assertEqual(doc.name, TEST_NAME)

	def test_disabled_record_is_excluded_from_default_query(self):
		self._make(disabled=1)
		results = frappe.get_all("Indian Postal Code", filters={"pincode": TEST_PINCODE, "disabled": 0})
		self.assertEqual(len(results), 0)
