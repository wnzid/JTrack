# JTrack

JTrack is a role-aware student operations workspace for monitoring applications, offers, enrollments, agents, course classifications, offer expiry, and visa status. It keeps a server-rendered Flask interface close to the underlying rows and can read from SQLite, Excel, or an optional SharePoint workbook.

## What changed

The current version replaces the original single-file prototype with a maintainable application structure while preserving its routes and reporting purpose.

- Flask application factory with page, authentication, API, data, and database boundaries.
- Manager and Leader authorization on both report pages and their JSON endpoints.
- CSRF-protected account forms, POST-only sign-out, hardened cookies, safe redirects, and production secret enforcement.
- Stable `{data, meta}` API responses with legacy array mode, source metadata, and bounded raw-data pagination.
- Atomic Excel-to-SQLite ETL with normalized columns, indexes, and generated report views.
- One responsive interface and report system instead of page-specific Bootstrap/glassmorphism layers.
- Accessible loading, empty, error, keyboard-focus, reduced-motion, table, chart, and export states.
- A browser-persisted custom view builder.
- Pytest coverage, Ruff checks, and GitHub Actions quality gates.

## Architecture

```text
Backend/
├── app.py                         # Compatible development / WSGI entry point
├── etl_load_from_excel_to_sqlite.py
├── jtrack/
│   ├── __init__.py                # create_app()
│   ├── api.py                     # Authenticated JSON endpoints
│   ├── auth.py                    # Registration, sign-in, sign-out
│   ├── config.py                  # Environment configuration
│   ├── data.py                    # SQLite, Excel, SharePoint adapters
│   ├── database.py                # User DB and admin CLI
│   ├── pages.py                   # Server-rendered routes
│   ├── reports.py                 # Canonical report catalog and SQL
│   └── security.py                # Role and CSRF controls
├── static/Css/app.css             # Product design system
├── static/Js/                     # Shared API, charts, reports, builder
├── templates/                     # Shared shell and focused pages
└── tests/
```

## Local setup

JTrack supports Python 3.11 and newer.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS / Linux: source .venv/bin/activate
python -m pip install -r Backend/requirements-dev.txt
```

Copy `.env.example` to `Backend/.env`, then set a long random `SECRET_KEY`. Development will generate an ephemeral key if it is absent; production refuses to start without one.

### Prepare analytics data

The application can read the bundled workbook directly. Generating SQLite first provides indexed queries and report views:

```bash
python Backend/etl_load_from_excel_to_sqlite.py
```

Custom paths are supported:

```bash
python Backend/etl_load_from_excel_to_sqlite.py --source path/to/input.xlsx --destination path/to/analytics.db
```

### Run

```bash
python Backend/app.py
```

Open [http://127.0.0.1:5001](http://127.0.0.1:5001). A health check is available at `/health`.

## Accounts and production enrollment

Development allows registration and role selection by default to preserve the original demo workflow. Production defaults both off. Create production accounts from the application CLI:

```bash
cd Backend
flask --app app create-user
```

You can independently configure `ALLOW_REGISTRATION`, `ALLOW_ROLE_SELECTION`, and `DEFAULT_REGISTRATION_ROLE`. Never expose role self-selection on an untrusted public deployment.

## Configuration

| Variable | Purpose | Default |
| --- | --- | --- |
| `JTRACK_ENV` | `development` or `production` behavior | `development` |
| `SECRET_KEY` | Signs sessions; required in production | generated in development |
| `ANALYTICS_DATABASE` | SQLite analytics path | `Backend/dummy_data.db` |
| `EXCEL_DATA_PATH` | Excel fallback path | `Backend/dummy_data.xlsx` |
| `USERS_DATABASE` | Account database path | `Backend/instance/users.db` |
| `DEFAULT_SQLITE_TABLE` | Raw-data table override | first user table |
| `API_MAX_PAGE_SIZE` | Maximum `/api/data` page size | `500` |
| `ALLOW_REGISTRATION` | Enables the registration page | on in development |
| `ALLOW_ROLE_SELECTION` | Allows self-selected roles | on in development |
| `SESSION_COOKIE_SECURE` | HTTPS-only session cookie | on in production |
| `USE_SHAREPOINT` | Reads the configured SharePoint workbook | `false` |

SharePoint additionally requires `SP_CLIENT_ID`, `SP_CLIENT_SECRET`, `SP_SITE_URL`, and `SP_FILE_PATH`, plus `python -m pip install -r Backend/requirements-sharepoint.txt`.

## API contract

Authenticated API responses use a consistent envelope:

```json
{
  "data": [{ "status": "Offered", "total": 42 }],
  "meta": {
    "count": 1,
    "generated_at": "2026-09-11T12:00:00+00:00",
    "source": "sqlite",
    "report": "application-status"
  }
}
```

Append `?legacy=1` to report endpoints during migration if an existing integration still expects a bare JSON array. `/api/data` also accepts `page` and `per_page`.

## Quality checks

```bash
python -m ruff check Backend
python -m pytest
python -m compileall -q Backend
```

GitHub Actions runs lint and tests on every pull request and pushes to `main`.

## Security notes

- Keep secrets in `Backend/.env`; it is ignored by Git.
- Run production behind HTTPS and keep `SESSION_COOKIE_SECURE=true`.
- Disable public registration unless the deployment is an intentionally isolated demo.
- The bundled workbook is sample data. Review source files before committing real student information.

## License

No license is currently declared. Contact the repository owner before redistributing the project.
