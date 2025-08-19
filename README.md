# JTrack

JTrack is a lightweight dashboard and API for tracking student applications and offers. It combines a Flask web interface with a data pipeline that loads Excel workbooks into a SQLite database and exposes metrics through JSON endpoints.

## Features

- **Flask web application** with role‑based access control.
- **Data ingestion pipeline** for converting Excel sheets into a SQLite database.
- **RESTful API endpoints** providing statistics such as application status, agent performance, and visa breakdowns.
- **Optional SharePoint integration** for reading data directly from Microsoft SharePoint.
- **Extensible templates and static assets** for building custom dashboards.

## Project Structure

```
Backend/
├── app.py                      # Main Flask application
├── dummy_data.xlsx             # Sample data source
├── etl_load_from_excel_to_sqlite.py  # Excel → SQLite loader
├── requirements.txt            # Python dependencies
├── static/                     # CSS/JS assets
└── templates/                  # HTML templates
```

## Prerequisites

- Python 3.11 or later
- pip

## Setup

1. **Install dependencies**
   ```bash
   pip install -r Backend/requirements.txt
   ```

2. **Generate the SQLite database** (from the provided Excel sample):
   ```bash
   python Backend/etl_load_from_excel_to_sqlite.py
   ```

## Running the Application

Start the Flask development server:
```bash
python Backend/app.py
```
The server listens on [http://localhost:5001](http://localhost:5001).

## Environment Variables

The application reads configuration from environment variables. Common settings include:

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | Flask session secret. |
| `USE_SHAREPOINT` | Set to `true` to read data from SharePoint. |
| `DEFAULT_SQLITE_TABLE` | Override default table when querying SQLite. |
| `SP_CLIENT_ID`, `SP_CLIENT_SECRET`, `SP_SITE_URL`, `SP_FILE_PATH` | Credentials and location for SharePoint data. |

Create a `.env` file in `Backend/` to store these values for development.

## User Management

Users are stored in `users.db`. Use the `Backend/view-users.py` script to view existing accounts. The `app.py` module seeds the database on startup if it does not exist.

## Contributing

Contributions, issues and feature requests are welcome! Feel free to check the issues page if you want to contribute.

## License

This project is provided "as is" without a specific license. Please contact the authors for reuse permissions.

