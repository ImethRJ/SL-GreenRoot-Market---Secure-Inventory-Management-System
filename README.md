# SL-GreenRoot Market - Secure Inventory Management System

A secure, full-stack Inventory Management System built for **"SL-GreenRoot Market"** (a Sri Lankan supermarket) using Python, Django, and Tailwind CSS. The application features strict HTML/Markdown sanitization, Role-Based Access Control (RBAC), cookie hardening, a cashier terminal (POS) Checkout page, production static asset delivery with WhiteNoise, and cloud deployment compatibility for Vercel and PostgreSQL / Supabase.

> 🌐 **Live Production Application:** [https://green-root-market.vercel.app/](https://green-root-market.vercel.app/)

---

## 🛠️ Technical Profile & Specifications

*   **Language Stack Used:** Python 3.11+, JavaScript (Vanilla ES6), HTML5, CSS3.
*   **Frameworks & Server:** Django 5.0 (Full-Stack MVC Backend), Tailwind CSS v3 (Responsive Design Engine), WhiteNoise (Production Static Asset Handling).
*   **Deployment Platforms:** Vercel (Serverless WSGI), Supabase / PostgreSQL (Cloud Database).
*   **Libraries Used:** 
    *   `nh3`: High-performance Rust-based HTML sanitization engine.
    *   `markdown`: Compiles raw text notes inputs into standardized HTML.
    *   `Pillow`: Image processing library managing product thumbnail media assets.
    *   `python-dotenv`: Injects credentials into settings from local configuration files.
    *   `whitenoise`: High-performance static file serving directly from Django WSGI without separate web server configuration.
    *   `dj-database-url`: Environment-driven database connection string parser (`DATABASE_URL`).
    *   `psycopg2-binary`: PostgreSQL database driver for Supabase / production relational databases.
*   **Security Used:** 
    *   **Dual-Pass XSS Protection:** Markdown inputs are compiled and sanitized via `nh3` strict allowlist before storage.
    *   **Role-Based Access Control (RBAC):** Group authorization decorators (`@manager_required`, `@cashier_or_manager_required`) that filter incoming HTTP requests.
    *   **Cookie Hardening:** Strict browser transport configurations (`HttpOnly` session/CSRF cookies, SameSite `Lax`).
    *   **CSRF Controls:** Automated CSRF token parsing on POS JavaScript checkout postings and forms.
*   **ORM & Database Handling:** 
    *   Django ORM with atomicity safeguards (`transaction.atomic` on checkouts).
    *   Dynamic database backend configuration via `dj-database-url`:
        *   **Local Development:** SQLite (`sqlite:///db.sqlite3`).
        *   **Production Deployment:** PostgreSQL / Supabase with persistent connection pooling (`conn_max_age=600`) and connection health checks.

---

## 🚀 Quick Start Guide

> [!NOTE]
> Environment configurations (`.env`), Python virtual environments (`.venv`), and local SQLite database files (`db.sqlite3`) are excluded from Git version control (`.gitignore`). Follow the steps below when cloning or setting up the repository locally.

### 1. Initialize Virtual Environment & Install Dependencies
First, set up your Python virtual environment and install the required modules:
```bash
# Create the virtual environment
python -m venv .venv

# Activate and install dependencies (Windows)
.venv\Scripts\pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` to create your local environment file:
```bash
# Create local environment file
cp .env.example .env
```
Default `.env` configuration:
```env
DEBUG=True
SECRET_KEY=django-insecure-greenroot-market-super-secret-key-12345
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 3. Set Up Database Schema
Run migrations to build the database tables and initialize default user roles:
```bash
.venv\Scripts\python manage.py migrate
```

### 4. Seed Initial Store Data & User Accounts
Seed default categories, products, and default staff credentials:
```bash
.venv\Scripts\python seed.py
```

### 5. Run the Application
Start the Django development server:
```bash
.venv\Scripts\python manage.py runserver
```
Visit the staff portal at **`http://127.0.0.1:8000/`**.

---

## 🌐 Production & Vercel Deployment

* **Live Deployment URL:** [https://green-root-market.vercel.app/](https://green-root-market.vercel.app/)

This repository is pre-configured for seamless deployment to **Vercel** with a **Supabase / PostgreSQL** cloud database.

### Build Script & Static Assets (`build_files.sh`)
Vercel executes `build_files.sh` on deployment to install Python dependencies, build minified Tailwind CSS assets, and run Django `collectstatic`:
```bash
#!/bin/bash
python3 -m pip install -r requirements.txt
npx -y tailwindcss@3 -i ./inventory/static/css/input.css -o ./inventory/static/css/tailwind.css --minify
python3 manage.py collectstatic --no-input --clear
```

### Serverless Routing (`vercel.json`)
The WSGI application handler `greenroot_market/wsgi.py` routes incoming serverless requests through Vercel:
```json
{
  "buildCommand": "bash build_files.sh",
  "outputDirectory": "staticfiles",
  "routes": [
    { "src": "/static/(.*)", "dest": "/static/$1" },
    { "src": "/(.*)", "dest": "greenroot_market/wsgi.py" }
  ]
}
```

### Production Environment Variables on Vercel
Set the following environment variables in your Vercel project settings:
* `DATABASE_URL`: `postgresql://<user>:<password>@<host>:5432/<dbname>` (e.g., Supabase connection string)
* `SECRET_KEY`: `<your-random-production-secret-key>`
* `DEBUG`: `False`

---

## 🔑 Login Accounts (All passwords: `pwd`)

Logging in with different users alters access permissions based on Role-Based Access Control (RBAC):

| Role | Username | Password | Access Rights & Restrictions |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `pwd` | Full storefront CRUD, access to Django Admin Panel (`/admin/`), user accounts management. |
| **Manager** | `manager` | `pwd` | Full product CRUD, dashboard KPIs, transaction logs. Blocked from Django Admin Panel. |
| **Cashier** | `cashier` | `pwd` | POS terminal window checkout and catalog search only. Blocked from adding/editing products. |

To manually create a custom superuser admin, run:
```bash
.venv\Scripts\python manage.py createsuperuser
```

---

## 🛡️ Key Security Features & Constraints

1. **Dual-Pass HTML Sanitization (Stored XSS Protection):**
   Product supplier and batch notes submitted in Markdown are compiled into HTML on the backend, then sanitized with the Rust-powered `nh3` clean engine using a strict allowlist:
   * **Allowed Tags:** `p, br, strong, em, u, h1-h6, ul, ol, li, code, pre, blockquote, a, hr, table, thead, tbody, tr, th, td, del, span, div`.
   * All script, iframe, styling elements, and malicious event-handler attributes are stripped to prevent Stored XSS.
2. **Template Safety:**
   Rich HTML rendering uses the `|safe` tag ONLY after validation and sanitization has occurred in the backend. 
3. **Cookie Hardening:**
   CSRF and Session cookies are secured against hijacking in `settings.py`:
   - `CSRF_COOKIE_HTTPONLY = True`
   - `SESSION_COOKIE_HTTPONLY = True`
   - `CSRF_COOKIE_SAMESITE = 'Lax'`
4. **Access Control:**
   Managerial views are locked with `@manager_required`, which returns a `403 Forbidden` response to unauthorized users like Cashiers.

---

## 📂 Core Folder Structure

```text
greenroot_market/
├── greenroot_market/     # Project Configuration
│   ├── settings.py       # Hardened cookies, dj-database-url, WhiteNoise, app registration
│   ├── urls.py           # Main routing & Admin Console url path
│   └── wsgi.py           # Entry point for WSGI web servers and Vercel serverless functions
├── inventory/            # Supermarket Application logic
│   ├── models.py         # Category, Product (overridden save()), StockTransaction ORM Models
│   ├── views.py          # Dashboard view, Catalog view, POS cashier API checkout endpoints
│   ├── urls.py           # Store routing patterns
│   ├── utils.py          # Dual-pass nh3 clean helper & custom RBAC decorators
│   ├── forms.py          # ProductForm with inline Tailwind styles
│   ├── templates/        # Store HTML views
│   │   └── inventory/
│   │       ├── base.html              # Outfitted layout template
│   │       ├── dashboard.html         # Key indicators & recent transaction logs
│   │       ├── product_list.html      # Product catalog with live search API
│   │       ├── product_form.html      # Create/Edit product pages
│   │       ├── product_confirm_delete.html
│   │       ├── login.html             # Staff portal login
│   │       └── pos.html               # Cashier POS terminal layout
│   └── static/
│       ├── css/
│       │   ├── input.css              # Source Tailwind CSS directive
│       │   └── tailwind.css           # Compiled minified stylesheet
│       └── js/
│           └── pos_search.js          # Cart state, AJAX checkout postings
├── build_files.sh        # Vercel deployment automation script
├── vercel.json           # Vercel serverless routing configuration
├── tailwind.config.js    # Tailwind CSS scanning and theme setup
├── requirements.txt      # Django, WhiteNoise, dj-database-url, psycopg2-binary, nh3, etc.
├── seed.py               # Seed database automation script
├── .env.example          # Environment settings template
└── manage.py
```

---

## 🧪 Testing and Verification

Run the automated tests to verify security controls, role routes, search queries, and transactional integrity:
```bash
.venv\Scripts\python manage.py test
```
Ran 7 tests successfully with a 100% pass rate.
