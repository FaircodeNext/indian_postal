// Copyright (c) 2026, FaircodeNext Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Indian Postal Code", {
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}

		frm.add_custom_button(__("Fetch Latest Data"), () => {
			frappe.dom.freeze(__("Fetching latest postal data..."));
			frm.call("fetch_latest_data")
				.then(() => {
					frappe.show_alert({ message: __("Postal data refreshed."), indicator: "green" });
					frm.reload_doc();
				})
				.finally(() => frappe.dom.unfreeze());
		});
	},
});
