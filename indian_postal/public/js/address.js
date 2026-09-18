// Copyright (c) 2026, FaircodeNext Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Address", {
	refresh(frm) {
		frm.add_custom_button(__("Fetch Postal Details"), () => {
			fetch_postal_details(frm, { silent: false, force: false });
		});

		frm.set_query("custom_post_office", () => ({
			filters: Object.assign({ disabled: 0 }, frm.doc.pincode ? { pincode: frm.doc.pincode } : {}),
		}));
	},

	pincode(frm) {
		fetch_postal_details(frm, { silent: true, force: false });
	},

	custom_post_office(frm) {
		if (!frm.doc.custom_post_office) {
			return;
		}
		frappe.call({
			method: "indian_postal.api.postal.get_post_office",
			args: { name: frm.doc.custom_post_office },
			callback(r) {
				if (r.message) {
					apply_post_office(frm, r.message);
				}
			},
		});
	},
});

function fetch_postal_details(frm, { silent = false, force = false } = {}) {
	const pincode = (frm.doc.pincode || "").trim();
	if (!/^\d{6}$/.test(pincode)) {
		if (!silent) {
			frappe.msgprint(__("Please enter a valid 6 digit PIN code."));
		}
		return;
	}

	frappe.call({
		method: "indian_postal.api.postal.get_postal_details",
		args: { pincode, force_refresh: force ? 1 : 0 },
		freeze: !silent,
		freeze_message: __("Fetching postal details..."),
		callback(r) {
			const data = r.message;
			if (!data || !data.post_offices || !data.post_offices.length) {
				return;
			}

			if (data.post_offices.length === 1) {
				apply_post_office(frm, data.post_offices[0]);
			} else {
				show_post_office_dialog(frm, data.post_offices);
			}
		},
	});
}

function show_post_office_dialog(frm, post_offices) {
	const options = post_offices.map(
		(po) => `${po.post_office_name} - ${po.branch_type || ""} - ${po.delivery_status || ""}`
	);

	const dialog = new frappe.ui.Dialog({
		title: __("Select Post Office"),
		fields: [
			{
				fieldname: "post_office",
				fieldtype: "Select",
				label: __("Post Office"),
				options: options,
				reqd: 1,
			},
		],
		primary_action_label: __("Select"),
		primary_action(values) {
			const index = options.indexOf(values.post_office);
			apply_post_office(frm, post_offices[index]);
			dialog.hide();
		},
	});

	dialog.set_value("post_office", options[0]);
	dialog.show();
}

function apply_post_office(frm, post_office) {
	frm.set_value({
		custom_post_office: post_office.name,
		custom_branch_type: post_office.branch_type,
		custom_delivery_status: post_office.delivery_status,
		custom_postal_circle: post_office.circle,
		custom_postal_district: post_office.district,
		custom_postal_division: post_office.division,
		custom_postal_region: post_office.region,
		custom_postal_block: post_office.block,
		state: post_office.state,
		country: post_office.country,
	});
}
