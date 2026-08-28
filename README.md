# Vulnerability Alert Management Dashboard

Starter Streamlit project for an interactive vulnerability remediation dashboard.

## Business rules

- **RRD** = final remediation date.
- **2-Week Mark** = operational due date used by the team.
- Expected **2-Week Mark = RRD - 14 calendar days**.
- **ATC** = Application Technical Contact.
- The app preserves VVMS source fields and creates separate derived fields.

## Included files

- `app.py` — interactive Streamlit dashboard and spreadsheet workspace
- `data_model.py` — cleaning, calculations, filtering, KPIs, priority logic
- `integration_template.py` — handoff/specification script for another developer
- `sample_vvms.csv` — synthetic test data using the required schema
- `requirements.txt` — Python dependencies

## Features

- CSV upload
- Interactive sidebar filters
- Search across IDs, title, application, ATC and host
- KPI cards
- Remediation urgency charts
- Application/environment/ATC charts
- Priority remediation queue
- Spreadsheet-style findings workspace
- Select a row to inspect finding details
- Download filtered results
- Data-quality checks for:
  - RRD vs 2-Week Mark
  - VVMS Days Left vs calculated Days Left
  - missing deadline/contact fields

## Run

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

The app automatically opens `sample_vvms.csv` until a VVMS CSV is uploaded.

## Important

Do not commit real production vulnerability data, server names, contacts, or
other sensitive internal information to a public GitHub repository. Use
synthetic or sanitized data for development and portfolio examples.

## Template influences

This starter project is an original implementation inspired by the general
interaction patterns of:

- Data Professor `dashboard-kit`: wide Streamlit KPI/dashboard layout,
  timeframe/data-table concepts.
- Sven-Bo `streamlit-sales-dashboard`: spreadsheet-backed dashboard,
  dynamic filtering and KPI-driven exploration.

The business logic and VVMS-specific implementation are customized for this
vulnerability alert management workflow.
