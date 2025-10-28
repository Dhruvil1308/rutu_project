# Product Recommendation System

This project exposes a Flask-based web experience for an ecommerce catalogue and includes a content-based product recommender that blends textual similarity with lightweight popularity signals.

## Project Highlights

- **Content-based recommendations** built with TF-IDF features spanning product name, brand, category, tags, and marketing copy.
- **Popularity-aware re-ranking** using product rating and log-transformed review volumes.
- **Fuzzy search fallback** to handle typos and suggestions when an exact product match is unavailable.
- **Modular architecture** (`config.py`, `recommendation.py`, templates, static assets) for easier maintenance and extension.
- **Secure MySQL-backed authentication** with hashed passwords, session management, and login gating before recommendation access.

## Repository Layout

```
app.py                 # Flask application with routes and dependency wiring
config.py              # Shared configuration helpers and constants
recommendation.py      # Recommendation engine implementation
requirements.txt       # Python dependencies
templates/             # Jinja2 templates (base, dashboard, auth pages, partials)
static/js/main.js      # Front-end behaviour for settings/zoom actions
schema.sql             # MySQL bootstrap script for phpMyAdmin import
clean_data.csv         # Sample catalogue used for training the recommender
trending_products.csv  # Sample trending products for homepage carousel
```

## Data Expectations

- `clean_data.csv` should contain at least the columns `Name`, `Brand`, `Category`, `Tags`, `Description`, `Rating`, and `ReviewCount`.
- `trending_products.csv` powers the homepage highlights. Only the first pipe-separated image in `ImageURL` is used; ensure URLs are valid.
- Place datasets in either the project root (`./`) or a `./data/` folder. The application attempts both locations automatically.

## Environment Setup

1. **Create a virtual environment (recommended):**

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. **Install dependencies:**

   ```powershell
   pip install -r requirements.txt
   ```

3. **Provision the database:**

   - Import `schema.sql` into phpMyAdmin (XAMPP) to create the `product_recommendation_system` schema and `users` table.
   - Update `SQLALCHEMY_DATABASE_URI` in `app.py` if your MySQL credentials differ from `mysql://root:@localhost/product_recommendation_system`.
   - Alternatively, initialise via SQLAlchemy:

     ```powershell
     python - <<'PY'
     from app import db
     db.create_all()
     PY
     ```

4. **Run the Flask server:**

   ```powershell
   set FLASK_APP=app.py
   set FLASK_ENV=development
   flask run
   ```

   Navigate to <http://127.0.0.1:5000/> to access the UI.

## Evaluating Recommendation Quality

`recommendation.py` exposes a `ProductRecommender` class that you can probe from a notebook or REPL:

```python
from recommendation import ProductRecommender

recommender = ProductRecommender()
response = recommender.recommend("OPI Infinite Shine, Nail Lacquer Nail Polish, Bubble Bath", top_n=5)
print(response.results[["Name", "score", "similarity", "popularity"]])
```

Consider the following guidelines for sustained quality:

- **Data hygiene:** ensure textual fields are complete; missing descriptions hurt coverage. Enrich sparse products where possible.
- **Vocabulary size:** adjust `TFIDF_MAX_FEATURES` or `TFIDF_MIN_DF` in `config.py` for larger catalogues.
- **Popularity weight:** tune `SIMILARITY_WEIGHT` to balance textual similarity and business-driven popularity.
- **Offline validation:** craft hold-out sets (e.g., purchase logs) once available and validate using ranking metrics such as MAP@K or NDCG@K.

## Smooth Operations Checklist

- Keep dependencies pinned in `requirements.txt` and rebuild the virtual environment when upgrading.
- Periodically refresh `clean_data.csv` with the latest catalogue and retrigger the recommender (restart Flask to rebuild the TF-IDF model).
- Monitor logs for 
  `FileNotFoundError` messages—these indicate missing datasets or misnamed files.
- Move configuration secrets (database credentials, secret key) into environment variables before deploying publicly.

## Next Steps

- Extend the user model with roles or personalization toggles to tailor recommendations by segment.
- Add analytics endpoints to surface top-performing products and track recommendation click-throughs.
- Containerise the application (Docker + Gunicorn) for deployment consistency once satisfied with accuracy and performance.
