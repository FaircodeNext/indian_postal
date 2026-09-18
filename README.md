<div align="center">
  <img src="indian_postal/public/images/indian_postal-logo.png" width="120" height="120" alt="Indian Postal logo">

  <h3>Indian Postal</h3>
  <p>Indian PIN code &amp; Post Office lookup for Frappe/ERPNext Address forms.</p>
</div>

## What it does

Indian Postal adds an Indian PIN code and Post Office master to Frappe/ERPNext and wires
it into the standard **Address** doctype. Enter a 6-digit PIN code on an Address and the
app fills in the Post Office, Branch Type, Delivery Status, Circle, District, Division,
Region, Block, State and Country automatically — no manual typing, no copy-pasting from
the India Post website.

Data is looked up from a local cache first (the **Indian Postal Code** doctype) and only
falls back to the public [PostalPincode API](https://www.postalpincode.in/Api-Details) on
a cache miss. Every response returned by the API is saved back to the cache, so a PIN code
is only ever fetched from the internet once across your entire site.

### Features

- **Auto-fill on PIN code entry** — type a PIN code on any Address, the Post Office and
  postal fields populate automatically.
- **Handles multiple Post Offices per PIN code** — a dialog lets the user pick the right
  one when a PIN code covers more than one Post Office (common for Indian PIN codes).
- **Local-first, API-backed cache** — the external API is only called on a cache miss or
  an explicit refresh; every other lookup is a local database read.
- **No direct browser-to-internet calls** — the external API is only ever called from the
  server, through a whitelisted method, never from client-side JavaScript.
- **Manual refresh** — a "Fetch Postal Details" button on Address and a "Fetch Latest
  Data" button on Indian Postal Code let you force a refresh from the API at any time.
- **Searchable Post Office master** — the Post Office field is a proper Link field,
  filtered to the entered PIN code, and searchable by post office name, PIN code,
  district or state.
- **Friendly error handling** — invalid PIN codes, timeouts and an unreachable API all
  surface a plain-language message instead of a traceback.

### Screenshots

> _Add screenshots here before submitting to the Marketplace:_
> 1. An Address form with a PIN code entered and the Postal Information section populated.
> 2. The "Select Post Office" dialog when a PIN code has multiple Post Offices.
> 3. The Indian Postal Code list/report view.

## Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch version-16
bench --site $SITE_NAME install-app indian_postal
bench --site $SITE_NAME migrate
```

### Manual test

```bash
bench --site $SITE_NAME console
```
```python
from indian_postal.api.postal import get_postal_details
get_postal_details("683513")
```

Or over REST:

```
GET /api/method/indian_postal.api.postal.get_postal_details?pincode=683513
```

## How it works

```
ERPNext Address (PIN code entered)
        │
        ▼
Frappe client script (public/js/address.js)
        │  frappe.call()
        ▼
Whitelisted Python API (indian_postal.api.postal.get_postal_details)
        │
        ▼
Check local "Indian Postal Code" cache
    │                       │
    │ found                 │ not found
    ▼                       ▼
Return cached          Call api.postalpincode.in,
Post Office(s)         save results locally,
                        then return them
        │
        ▼
One Post Office → auto-fill Address
Multiple Post Offices → selection dialog → fill on choice
```

## Requirements

- Frappe Framework v16
- ERPNext v16 (for the Address doctype; the app itself has no other ERPNext dependency)
- Python 3.11+
- MariaDB

## Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/indian_postal
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### CI

This app uses GitHub Actions for CI. The following workflows are configured:

- **CI**: installs this app and runs its unit tests on every push to `version-16` and on every pull request.
- **Linters**: runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and [pip-audit](https://pypi.org/project/pip-audit/) on every pull request.

## License

mit
