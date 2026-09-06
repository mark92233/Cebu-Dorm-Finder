# Cebu Dorm Finder

A localized web platform designed to streamline accommodation discovery for students and young professionals in Cebu. The system indexes student dormitories, boarding houses, and rental listings, integrates geospatial views with institutional targeting, and includes automation scripts to source community listings directly from social platforms.

---

## Architecture & Modules

The platform is architected around a modular Django backend, organized into targeted applications:

* **`core/`**: Central application housing core routing, foundational templates, site-wide logic, and baseline web scraping utilities (`information_scraper.py`).
* **`accounts/`**: Authentication and identity management, supporting standard session auth, custom profile modeling, OTP-based verification workflows, and email-based activation routines.
* **`maps/`**: Spatial integration, institution-proximity searches, interactive mapping views, and listing aggregation scripts:
* `generate_auth_state.py`: Session extraction and credential state generator for crawler authentication.
* `scrape_fb_groups.py`: Automated scraper targeted at Cebu dormitory and rental Facebook groups to ingest community-sourced listings directly into the listing database.


* **`dormFinder/`**: Master Django configuration directory handling project settings (`settings.py`), master routing (`urls.py`), WSGI/ASGI gateways, and institution-specific search controllers (`school_search.html`).

---

## Tech Stack

* **Backend**: Python 3.13, Django
* **Database**: SQLite (default / development), compatible with PostgreSQL / MySQL
* **Frontend**: HTML5, Django Template Engine, Tailwind CSS / Custom CSS, Vanilla JavaScript
* **Mapping**: Leaflet.js / OpenStreetMap or Google Maps API integration
* **Automation & Scraping**: Playwright / Selenium / BeautifulSoup4 for community listing ingestion

---

## Project Structure

```text
Cebu-Dorm-Finder/
├── accounts/                  # User management, OTP verification, profiles
│   ├── migrations/
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   ├── utils.py
│   └── views.py
├── core/                      # Core views, common utilities, general scrapers
│   ├── information_scraper.py
│   ├── models.py
│   └── views.py
├── dormFinder/                # Django project orchestrator
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   ├── views.py
│   └── wsgi.py
├── maps/                      # Map rendering, spatial filtering, Facebook scrapers
│   ├── generate_auth_state.py
│   ├── scrape_fb_groups.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── static/                    # Global assets, media, styles
│   └── img/
├── .env                       # Environment variables (git-ignored)
├── db.sqlite3                 # Local SQLite database
└── manage.py                  # Django CLI entrypoint

```

---

## Getting Started

### Prerequisites

* **Python 3.11+** (Python 3.13 recommended)
* **Virtual Environment Tool** (`venv` or `virtualenv`)
* **Browser Driver Engine** (Chromium / Playwright if running listing scrapers)

### 1. Clone & Environment Setup

```bash
git clone https://github.com/your-username/Cebu-Dorm-Finder.git
cd Cebu-Dorm-Finder

# Initialize virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

```

### 2. Install Dependencies

```bash
pip install -r requirements.txt

```

*(If `requirements.txt` is not yet bundled, install the core baseline: `pip install django python-dotenv playwright beautifulsoup4 requests`)*

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
DEBUG=True
SECRET_KEY=your-secure-django-secret-key
ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=sqlite:///db.sqlite3

# Email verification (for accounts/account_activation_email.html)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

```

### 4. Database Migrations

Run database migrations to initialize identity, listings, and social post tables:

```bash
python manage.py makemigrations
python manage.py migrate

```

### 5. Create Superuser & Run Development Server

```bash
python manage.py createsuperuser
python manage.py runserver

```

Navigate to `[http://127.0.0.1:8000/](http://127.0.0.1:8000/)` in your browser. Access the administration dashboard at `[http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)`.

---

## Scraping & Community Listings Automation

The platform includes background scraping utilities in the `maps/` directory to ingest listings from rental groups:

1. **Generate Session State**:
```bash
python maps/generate_auth_state.py

```


*Captures necessary cookie and local authentication tokens into a secure state file.*
2. **Execute Listing Harvester**:
```bash
python maps/scrape_fb_groups.py

```


*Parses recent posts, extracts pricing, location details, and contact numbers, and maps them to the `FacebookPost` model database.*

---

## Key Features

* **University Proximity Filtering**: Find accommodations indexed near major Cebu educational hubs (e.g., UC Main/Banilad, USC, USJ-R, UV, CNU, UP Cebu).
* **Interactive Map Viewer**: Visual coordinates and radius filters for quick spatial evaluation.
* **OTP & Email Activation**: Secured sign-up flows for student tenants and property owners.
* **Social Ingestion Pipeline**: Continually aggregates active sublet and dorm postings from community channels to maintain listing freshness.
