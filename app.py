"""Flask application wiring for the ecommerce recommendation demo."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List

import pandas as pd
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from werkzeug.security import check_password_hash, generate_password_hash

from config import DEFAULT_TOP_N, optional_data_path
from recommendation import ProductRecommender


app = Flask(__name__)


# Database configuration -----------------------------------------------------------
app.secret_key = "alskdjfwoeieiurlskdjfslkdjf"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:@localhost/product_recommendation_system"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"


class User(UserMixin, db.Model):
    """Application user stored in the backing MySQL database."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    if user_id and user_id.isdigit():
        return db.session.get(User, int(user_id))
    return None


def _load_trending_products(limit: int = 8) -> List[dict]:
    """Load trending product metadata for the homepage grid."""

    trending_path = optional_data_path("trending_products.csv")
    if not trending_path:
        return []

    trending = pd.read_csv(trending_path)
    trending = trending.head(limit).copy()
    trending["PrimaryImage"] = trending["ImageURL"].fillna("").apply(
        lambda value: value.split("|")[0].strip() if value else ""
    )
    return trending[["Name", "Brand", "Rating", "PrimaryImage", "ReviewCount"]].to_dict("records")


def truncate(text: str, length: int) -> str:
    return f"{text[:length]}..." if len(text) > length else text


try:
    recommender = ProductRecommender()
    recommender_available = True
    recommender_error = None
except FileNotFoundError as exc:
    recommender = None
    recommender_available = False
    recommender_error = str(exc)


@app.route("/")
@login_required
def index() -> str:
    trending = _load_trending_products()
    return render_template(
        "index.html",
        trending_products=trending,
        truncate=truncate,
        recommender_available=recommender_available,
        recommender_error=None if recommender_available else recommender_error,
    )


@app.route("/index")
@login_required
def indexredirect() -> str:
    return redirect(url_for("index"))


@app.route("/main")
@login_required
def main() -> str:
    trending = _load_trending_products()
    return render_template("main.html", trending_products=trending, truncate=truncate)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form_data: Dict[str, str] = {"username": "", "email": ""}
    errors: Dict[str, str] = {}

    if request.method == "POST":
        form_data["username"] = request.form.get("username", "").strip()
        form_data["email"] = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not form_data["username"]:
            errors["username"] = "Username is required."
        elif User.query.filter_by(username=form_data["username"]).first():
            errors["username"] = "Username already in use."

        if not form_data["email"]:
            errors["email"] = "Email address is required."
        elif User.query.filter_by(email=form_data["email"]).first():
            errors["email"] = "Email already registered."

        if len(password) < 8:
            errors["password"] = "Password must be at least 8 characters long."
        elif password != confirm_password:
            errors["confirm_password"] = "Passwords do not match."

        if not errors:
            user = User(username=form_data["username"], email=form_data["email"])
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))

        for message in errors.values():
            flash(message, "danger")

    return render_template("register.html", form=form_data, errors=errors)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        credential = request.form.get("credential", "").strip()
        password = request.form.get("password", "")

        user = None
        if credential:
            user = User.query.filter(
                or_(User.username == credential, User.email == credential.lower())
            ).first()

        if user and user.check_password(password):
            login_user(user)
            flash("Welcome back!", "success")
            next_url = request.args.get("next")
            return redirect(next_url or url_for("index"))

        flash("Invalid username/email or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("login"))


@app.route("/recommendations", methods=["POST"])
@login_required
def recommendations():
    if not recommender_available:
        return render_template(
            "main.html",
            message="Recommendation engine is not available. Please check data files.",
            truncate=truncate,
            trending_products=_load_trending_products(),
            recommendations=[],
            suggestions=[],
            resolved_name=None,
        )

    product_name = request.form.get("prod", "").strip()
    try:
        top_n = int(request.form.get("nbr", DEFAULT_TOP_N))
    except (TypeError, ValueError):
        top_n = DEFAULT_TOP_N

    response = recommender.recommend(product_name, top_n=top_n)

    if response.results.empty:
        return render_template(
            "main.html",
            message=response.message,
            suggestions=response.suggestions,
            truncate=truncate,
            trending_products=_load_trending_products(),
            recommendations=[],
            resolved_name=None,
        )

    recommendations_payload = response.results.to_dict("records")
    return render_template(
        "main.html",
        recommendations=recommendations_payload,
        resolved_name=response.resolved_name,
        truncate=truncate,
        trending_products=_load_trending_products(limit=4),
        suggestions=[],
        message=None,
    )


if __name__ == "__main__":
    app.run(debug=True)