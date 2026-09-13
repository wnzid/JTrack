<div align="center">
  <img src="Backend/static/Assets/logo.svg" width="84" alt="JTrack logo" />

# JTrack

**Operational reporting for the full student application journey.**

`Flask` · `SQLite` · `Excel` · `SharePoint optional` · `Role-aware`

</div>

JTrack is a student-operations workspace for applications, offers, enrolments, agents, course classification, offer expiry, and visa status. A server-rendered Flask interface stays close to the underlying rows and can read from SQLite, Excel, or an optional SharePoint workbook.

## Product capabilities

- Manager and Leader authorization on pages and JSON endpoints
- Report catalogue spanning the student lifecycle
- Responsive tables, charts, filtering, and export states
- Browser-persisted custom view builder
- Stable `{data, meta}` API envelopes with bounded pagination
- Atomic Excel-to-SQLite ETL with normalized columns, indexes, and report views
- CSRF-protected account flows, hardened cookies, and safe redirects
- Pytest, Ruff, and GitHub Actions quality gates

## Architecture

```text
Backend/
├── app.py                              Development / WSGI entry point
├── etl_load_from_excel_to_sqlite.py    Atomic data loader
├── jtrack/
│   ├── api.py                          Authenticated JSON endpoints
│   ├── auth.py                         Account workflows
│   ├── data.py                         SQLite, Excel, SharePoint adapters
│   ├── database.py                     User database and admin CLI
│   ├── pages.py                        Server-rendered routes
│   ├── reports.py                      Canonical reports and SQL
│   └── security.py                     Role and CSRF controls
├── static/                             Product styles and scripts
├── templates/                          Shared shell and pages
└── tests/                              Application and API tests
```

## Local setup

JTrack supports Python 3.11 and newer.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r Backend/requirements-dev.txt
```

Copy `.env.example` to `Backend/.env` and set a long random `SECRET_KEY`. Development can create an ephemeral key; production refuses to start without one.

Prepare the indexed analytics database and start the application:

```bash
python Backend/etl_load_from_excel_to_sqlite.py
python Backend/app.py
```

Open `http://127.0.0.1:5001`; health is available at `/health`.

## Configuration

| Variable | Purpose | Development default |
| --- | --- | --- |
| `JTRACK_ENV` | Runtime behavior | `development` |
| `SECRET_KEY` | Session signing | ephemeral outside production |
| `ANALYTICS_DATABASE` | SQLite analytics source | `Backend/dummy_data.db` |
| `EXCEL_DATA_PATH` | Excel fallback | `Backend/dummy_data.xlsx` |
| `USERS_DATABASE` | Account database | `Backend/instance/users.db` |
| `ALLOW_REGISTRATION` | Public registration | enabled |
| `ALLOW_ROLE_SELECTION` | Self-selected demo roles | enabled |
| `USE_SHAREPOINT` | SharePoint adapter | `false` |

Production defaults registration and role selection off. Create managed accounts with:

```bash
cd Backend
flask --app app create-user
```

## API shape

```json
{
  "data": [{ "status": "Offered", "total": 42 }],
  "meta": {
    "count": 1,
    "source": "sqlite",
    "report": "application-status"
  }
}
```

Append `?legacy=1` only for integrations that still require a bare array. `/api/data` supports `page` and `per_page`.

## Quality checks

```bash
python -m ruff check Backend
python -m pytest
python -m compileall -q Backend
```

## Security and data handling

- Keep secrets in `Backend/.env`; never commit real credentials.
- Use HTTPS and secure cookies in production.
- Keep public registration and role selection disabled on untrusted deployments.
- The bundled workbook is sample data; review every source before committing real student information.

## License

No license is currently declared. Contact the owner before redistribution.
