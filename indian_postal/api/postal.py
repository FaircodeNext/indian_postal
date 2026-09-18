import re

import frappe
from frappe import _
from frappe.utils import cint

POSTAL_API_BASE = "https://api.postalpincode.in"
REQUEST_TIMEOUT = 12

# API field -> Indian Postal Code fieldname
FIELD_MAP = {
	"Name": "post_office_name",
	"Description": "description",
	"BranchType": "branch_type",
	"DeliveryStatus": "delivery_status",
	"Circle": "circle",
	"District": "district",
	"Division": "division",
	"Region": "region",
	"Block": "block",
	"State": "state",
	"Country": "country",
	"Pincode": "pincode",
}

LOCAL_FIELDS = [
	"name",
	"pincode",
	"post_office_name",
	"description",
	"branch_type",
	"delivery_status",
	"circle",
	"district",
	"division",
	"region",
	"block",
	"state",
	"country",
]


def validate_pincode(pincode: str) -> str:
	"""Strip and validate a 6-digit Indian pincode, throwing a friendly error otherwise."""
	pincode = (pincode or "").strip()
	if not re.fullmatch(r"\d{6}", pincode):
		frappe.throw(_("Please enter a valid 6 digit PIN code."), title=_("Invalid PIN Code"))
	return pincode


def _get_local_records(pincode: str) -> list[dict]:
	return frappe.get_all(
		"Indian Postal Code",
		filters={"pincode": pincode, "disabled": 0},
		fields=LOCAL_FIELDS,
		order_by="post_office_name asc",
	)


def _call_postal_api(pincode: str) -> list[dict]:
	"""Call the external PostalPincode API for a pincode. Raises frappe.throw with a
	user-friendly message on any failure; technical details go to the error log."""
	import requests

	url = f"{POSTAL_API_BASE}/pincode/{pincode}"

	try:
		response = requests.get(
			url,
			timeout=REQUEST_TIMEOUT,
			headers={
				"Accept": "application/json",
				"User-Agent": "indian_postal-frappe-app/1.0",
			},
		)
		response.raise_for_status()
		data = response.json()
	except requests.exceptions.Timeout:
		frappe.log_error(title="Indian Postal: API Timeout", message=frappe.get_traceback())
		frappe.throw(_("Postal service is taking too long to respond. Please try again."))
	except requests.exceptions.RequestException:
		frappe.log_error(title="Indian Postal: API Connection Error", message=frappe.get_traceback())
		frappe.throw(_("Unable to connect to the postal service. Please try again later."))
	except ValueError:
		frappe.log_error(title="Indian Postal: Invalid API Response", message=frappe.get_traceback())
		frappe.throw(_("Unable to connect to the postal service. Please try again later."))

	if not data or not isinstance(data, list):
		frappe.log_error(title="Indian Postal: Empty API Response", message=str(data)[:1000])
		frappe.throw(_("No Post Office found for PIN code {0}.").format(pincode))

	result = data[0] or {}
	post_offices = result.get("PostOffice")
	if result.get("Status") != "Success" or not post_offices:
		frappe.throw(_("No Post Office found for PIN code {0}.").format(pincode))

	return post_offices


def _upsert_post_office(record: dict) -> str | None:
	"""Insert or update one Indian Postal Code record from an API PostOffice entry.
	Uses ignore_permissions because this write happens as a side effect of a Read-permitted
	lookup (get_postal_details) so the caller only needs Address/Read access, not
	Indian Postal Code/Write access, to populate the shared cache."""
	mapped = {fieldname: record.get(api_field) for api_field, fieldname in FIELD_MAP.items()}
	mapped = {k: (v.strip() if isinstance(v, str) else v) for k, v in mapped.items()}

	pincode = validate_pincode(mapped.get("pincode"))
	post_office_name = mapped.get("post_office_name")
	if not post_office_name:
		return None

	docname = f"{pincode}-{post_office_name}"
	if frappe.db.exists("Indian Postal Code", docname):
		doc = frappe.get_doc("Indian Postal Code", docname)
		for fieldname in FIELD_MAP.values():
			if fieldname in ("pincode", "post_office_name"):
				continue
			doc.set(fieldname, mapped.get(fieldname))
		doc.disabled = 0
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.new_doc("Indian Postal Code")
		doc.update(mapped)
		doc.insert(ignore_permissions=True)

	return doc.name


@frappe.whitelist()
def get_postal_details(pincode: str, force_refresh: int = 0) -> dict:
	"""Return Post Office details for an Indian pincode.

	Looks up the local Indian Postal Code cache first. Falls back to the external
	PostalPincode API only on a cache miss (or when force_refresh is set), then
	persists the API response locally so later lookups skip the external call.
	"""
	pincode = validate_pincode(pincode)
	force_refresh = cint(force_refresh)

	if not force_refresh:
		local = _get_local_records(pincode)
		if local:
			return {"source": "local", "pincode": pincode, "post_offices": local}

	post_offices = _call_postal_api(pincode)
	for record in post_offices:
		_upsert_post_office(record)

	return {"source": "api", "pincode": pincode, "post_offices": _get_local_records(pincode)}


@frappe.whitelist()
def search_post_office(txt: str = "", pincode: str | None = None) -> list[dict]:
	"""Search the local Indian Postal Code cache by post office name, pincode, district or state.

	Uses ignore_permissions (via frappe.get_all) because Indian Postal Code is a shared,
	non-sensitive reference master (public postal directory data) whose DocType permissions
	restrict direct desk/list access to System Manager. Any logged-in user filling an Address
	form still needs to look up post offices, so this narrow, whitelisted, read-only, max-20-row
	search is the intended access path instead of granting broader DocType-level read.
	"""
	txt = (txt or "").strip()
	filters = {"disabled": 0}
	if pincode:
		filters["pincode"] = validate_pincode(pincode)

	or_filters = None
	if txt:
		like = f"%{txt}%"
		or_filters = {
			"post_office_name": ["like", like],
			"pincode": ["like", like],
			"district": ["like", like],
			"state": ["like", like],
		}

	return frappe.get_all(
		"Indian Postal Code",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "post_office_name", "pincode", "district", "state"],
		order_by="post_office_name asc",
		limit=20,
	)


@frappe.whitelist()
def get_post_office(name: str) -> dict:
	"""Return the complete Indian Postal Code record for the given document name."""
	if not frappe.db.exists("Indian Postal Code", name):
		frappe.throw(_("Post Office record {0} not found.").format(name))
	return frappe.get_doc("Indian Postal Code", name).as_dict()
