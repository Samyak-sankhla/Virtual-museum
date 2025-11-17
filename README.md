# Virtual Museum — Flask + MySQL (DBMS Mini Project)

A small virtual museum web application built with Flask and MySQL. The app supports three roles (Admin, Artist, Customer), artifact uploads, exhibitions, shopping cart & purchases, and a small admin query runner for analytics.

---

## Quick Summary

- **Stack:** Python, Flask, MySQL
- **Entry point:** `app.py` (application factory in `create_app()`)
- **Templates:** `templates/`
- **Static files & uploads:** `static/` (uploads stored in `static/uploads`)

---

**Features (high level)**

- Multi-role user system: Admin / Artist / Customer
- Artists can upload artifacts with images
- Customers can browse artifacts, add to cart, and checkout
- Admin views: dashboard, transactions, run prebuilt SQL analytics queries
- File upload support with size/type limits and server-side image saving

---

**Repository Layout (key files)**

- `app.py` — application factory and run script
- `main.py` — main blueprint: dashboards, upload, cart, checkout, admin queries
- `auth.py` — authentication blueprint (login/logout/signup)
- `db.py` — database connection helpers and query helpers
- `config.py` — application settings (reads from `.env`)
- `queries/` — SQL helpers and complex query examples (`complex.sql`)
- `templates/` — Jinja2 HTML templates used by the app
- `static/uploads/` — uploaded artifact images
- `requirements.txt` — Python dependencies

---

Prerequisites

- Python 3.10+ (3.8+ should work, but use latest stable)
- MySQL server (5.7 / 8.0 recommended)
  
---

Installation (Windows / PowerShell)

1. Clone the repo and change directory:

```powershell
git clone <enter-your-credentials>
cd "Virtual-museum"
```

2. Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. Install Python dependencies:

```powershell
pip install -r requirements.txt
```

4. Create a `.env` file at the project root (example below) and update credentials:

```text
SECRET_KEY=replace-with-a-secret
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DB=virtual_museum
MYSQL_USER=<enter-your-credentials>
MYSQL_PASSWORD=<enter-your-credentials>
MYSQL_USER_READ=<enter-your-credentials>
MYSQL_PASSWORD_READ=<enter-your-credentials>
MYSQL_USER_ADMIN=m<enter-your-credentials>
MYSQL_PASSWORD_ADMIN=<enter-your-credentials>
```

These defaults come from `config.py`. Change them to secure values for production.

---

Database setup (example)

This project expects a MySQL database. You need to create the database and user(s). The following SQL is an example — adapt for your environment and strong passwords.

```sql
CREATE DATABASE IF NOT EXISTS virtual_museum CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- read/write admin (used by Admin role and migrations)
CREATE USER 'museum_admin'@'localhost' IDENTIFIED BY 'admin123';
GRANT ALL PRIVILEGES ON virtual_museum.* TO 'museum_admin'@'localhost';

-- limited application user (example)
CREATE USER 'museum_user'@'localhost' IDENTIFIED BY 'user123';
GRANT SELECT, INSERT, UPDATE, DELETE ON virtual_museum.* TO 'museum_user'@'localhost';

FLUSH PRIVILEGES;

To use the same database architecture -

Open MySQL cli & Run -

Source <path-to-file-code.sql>

code.sql is present in the repository.
```

Notes:
- The app relies on a schema (tables such as `User`, `Artifact`, `Purchase`, `Exhibition`, etc.). If you have a schema file, import it into `virtual_museum` first.

Run the application

From PowerShell (virtualenv active):

```powershell
# simple dev server (debug mode enabled in app.py)
python app.py
```

Open `http://127.0.0.1:5000/` in your browser. The app redirects unauthenticated users to login.

Configuration options

All runtime configuration is in `config.py` and reads environment variables via `.env` (see above). Important values:

- `SECRET_KEY` — Flask session secret (change this)
- `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DB`, `MYSQL_USER`, `MYSQL_PASSWORD` — DB connection
- `UPLOAD_FOLDER` — default is `static/uploads`
- `MAX_CONTENT_LENGTH` — file upload size limit (default 8 MB)
- `ALLOWED_EXTENSIONS` — allowed image extensions (`png`, `jpg`, `jpeg`, `webp`)

---

Troubleshooting

- If you get connection errors, verify MySQL is running and credentials in `.env` match created users.
- If uploads fail, ensure `static/uploads` exists and has write permission; the app will attempt to create it.
- Look at console logs where `python app.py` runs for Flask debug output.

---

Extending the project

- Add unit tests and CI configuration (e.g., GitHub Actions) to verify DB migrations and endpoints.
- Add schema SQL and migration support (Alembic or Flask-Migrate) for maintainability.
- Add pagination and richer search for artifacts and exhibitions.
- Some functionalities still need to be completed.
