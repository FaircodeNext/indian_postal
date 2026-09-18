# Copyright (c) 2026, FaircodeNext Technologies and Contributors
# See license.txt

from unittest.mock import MagicMock, patch

import frappe
import requests
from frappe.tests import IntegrationTestCase

from indian_postal.api.postal import (
	get_post_office,
	get_postal_details,
	search_post_office,
	validate_pincode,
)

TEST_PINCODE = "683513"

SAMPLE_API_RESPONSE = [
	{
		"Message": "Number of Post office(s) found:2",
		"Status": "Success",
		"PostOffice": [
			{
				"Name": "Ezhikkara",
				"Description": None,
				"BranchType": "Branch Post Office",
				"DeliveryStatus": "Delivery",
				"Circle": "Kerala",
				"District": "Ernakulam",
				"Division": "Alwaye",
				"Region": "Kochi",
				"Block": "Paravur",
				"State": "Kerala",
				"Country": "India",
				"Pincode": TEST_PINCODE,
			},
			{
				"Name": "Paravur",
				"Description": None,
				"BranchType": "Sub Post Office",
				"DeliveryStatus": "Delivery",
				"Circle": "Kerala",
				"District": "Ernakulam",
				"Division": "Alwaye",
				"Region": "Kochi",
				"Block": "Paravur",
				"State": "Kerala",
				"Country": "India",
				"Pincode": TEST_PINCODE,
			},
		],
	}
]


def _mock_response(json_data, status_ok=True):
	response = MagicMock()
	response.json.return_value = json_data
	response.raise_for_status = MagicMock() if status_ok else MagicMock(side_effect=requests.HTTPError)
	return response


class TestPostalApi(IntegrationTestCase):
	def tearDown(self):
		frappe.db.delete("Indian Postal Code", {"pincode": TEST_PINCODE})

	# -- validation -------------------------------------------------------

	def test_valid_pincode(self):
		self.assertEqual(validate_pincode("683513"), "683513")

	def test_pincode_with_whitespace_is_stripped(self):
		self.assertEqual(validate_pincode(" 683513 "), "683513")

	def test_short_pincode_is_invalid(self):
		with self.assertRaises(frappe.ValidationError):
			validate_pincode("68351")

	def test_alphabetic_pincode_is_invalid(self):
		with self.assertRaises(frappe.ValidationError):
			validate_pincode("ABCDEF")

	def test_pincode_with_letters_is_invalid(self):
		with self.assertRaises(frappe.ValidationError):
			validate_pincode("68351A")

	# -- local cache --------------------------------------------------------

	@patch("requests.get")
	def test_local_cache_hit_skips_external_api(self, mock_get):
		frappe.get_doc(
			{
				"doctype": "Indian Postal Code",
				"pincode": TEST_PINCODE,
				"post_office_name": "Ezhikkara",
				"state": "Kerala",
				"country": "India",
			}
		).insert()

		result = get_postal_details(TEST_PINCODE)

		self.assertEqual(result["source"], "local")
		self.assertEqual(len(result["post_offices"]), 1)
		mock_get.assert_not_called()

	# -- external API fallback ----------------------------------------------

	@patch("requests.get")
	def test_api_fallback_persists_multiple_post_offices(self, mock_get):
		mock_get.return_value = _mock_response(SAMPLE_API_RESPONSE)

		result = get_postal_details(TEST_PINCODE)

		self.assertEqual(result["source"], "api")
		self.assertEqual(len(result["post_offices"]), 2)
		self.assertTrue(frappe.db.exists("Indian Postal Code", f"{TEST_PINCODE}-Ezhikkara"))
		self.assertTrue(frappe.db.exists("Indian Postal Code", f"{TEST_PINCODE}-Paravur"))

	@patch("requests.get")
	def test_force_refresh_calls_api_even_when_cached(self, mock_get):
		frappe.get_doc(
			{
				"doctype": "Indian Postal Code",
				"pincode": TEST_PINCODE,
				"post_office_name": "Ezhikkara",
				"state": "Kerala",
				"country": "India",
			}
		).insert()
		mock_get.return_value = _mock_response(SAMPLE_API_RESPONSE)

		get_postal_details(TEST_PINCODE, force_refresh=1)

		mock_get.assert_called_once()

	@patch("requests.get")
	def test_refetch_updates_instead_of_duplicating(self, mock_get):
		mock_get.return_value = _mock_response(SAMPLE_API_RESPONSE)
		get_postal_details(TEST_PINCODE)
		get_postal_details(TEST_PINCODE, force_refresh=1)

		count = frappe.db.count("Indian Postal Code", {"pincode": TEST_PINCODE})
		self.assertEqual(count, 2)

	@patch("requests.get")
	def test_api_timeout_raises_friendly_error(self, mock_get):
		mock_get.side_effect = requests.exceptions.Timeout
		with self.assertRaises(frappe.ValidationError):
			get_postal_details(TEST_PINCODE)

	@patch("requests.get")
	def test_api_connection_error_raises_friendly_error(self, mock_get):
		mock_get.side_effect = requests.exceptions.ConnectionError
		with self.assertRaises(frappe.ValidationError):
			get_postal_details(TEST_PINCODE)

	@patch("requests.get")
	def test_empty_api_response_raises_friendly_error(self, mock_get):
		mock_get.return_value = _mock_response([])
		with self.assertRaises(frappe.ValidationError):
			get_postal_details(TEST_PINCODE)

	@patch("requests.get")
	def test_api_status_failure_raises_friendly_error(self, mock_get):
		mock_get.return_value = _mock_response([{"Status": "Error", "PostOffice": None}])
		with self.assertRaises(frappe.ValidationError):
			get_postal_details(TEST_PINCODE)

	# -- search / get ---------------------------------------------------------

	@patch("requests.get")
	def test_search_post_office_filters_by_pincode_and_text(self, mock_get):
		mock_get.return_value = _mock_response(SAMPLE_API_RESPONSE)
		get_postal_details(TEST_PINCODE)

		results = search_post_office(txt="Ezhik", pincode=TEST_PINCODE)

		self.assertEqual(len(results), 1)
		self.assertEqual(results[0]["post_office_name"], "Ezhikkara")

	@patch("requests.get")
	def test_get_post_office_returns_full_record(self, mock_get):
		mock_get.return_value = _mock_response(SAMPLE_API_RESPONSE)
		get_postal_details(TEST_PINCODE)

		record = get_post_office(f"{TEST_PINCODE}-Ezhikkara")

		self.assertEqual(record["district"], "Ernakulam")
		self.assertEqual(record["state"], "Kerala")

	def test_get_post_office_missing_record_raises(self):
		with self.assertRaises(frappe.ValidationError):
			get_post_office("999999-Nowhere")
