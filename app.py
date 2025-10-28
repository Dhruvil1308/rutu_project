"""Flask application wiring for the ecommerce recommendation demo."""
from __future__ import annotations

from typing import List

import pandas as pd
from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy

from config import DEFAULT_TOP_N, optional_data_path
from recommendation import ProductRecommender


app = Flask(__name__)


# Database configuration -----------------------------------------------------------
app.secret_key = "alskdjfwoeieiurlskdjfslkdjf"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:@localhost/ecom"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class Signup(db.Model):
    __tablename__ = "signup"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)


class Signin(db.Model):
    __tablename__ = "signin"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)


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
except FileNotFoundError as exc:
    recommender = None
    recommender_available = False
    recommender_error = str(exc)


@app.route("/")
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
def indexredirect() -> str:
    return redirect(url_for("index"))


@app.route("/main")
def main() -> str:
    trending = _load_trending_products()
    return render_template("main.html", trending_products=trending, truncate=truncate)


@app.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        new_signup = Signup(username=username, email=email, password=password)
        db.session.add(new_signup)
        db.session.commit()

        return render_template(
            "index.html",
            trending_products=_load_trending_products(),
            truncate=truncate,
            signup_message="User signed up successfully!",
            recommender_available=recommender_available,
            recommender_error=None if recommender_available else recommender_error,
        )

    return redirect(url_for("index"))


@app.route("/signin", methods=["POST", "GET"])
def signin():
    if request.method == "POST":
        username = request.form["signinUsername"]
        password = request.form["signinPassword"]

        new_signin = Signin(username=username, password=password)
        db.session.add(new_signin)
        db.session.commit()

        return render_template(
            "index.html",
            trending_products=_load_trending_products(),
            truncate=truncate,
            signup_message="User signed in successfully!",
            recommender_available=recommender_available,
            recommender_error=None if recommender_available else recommender_error,
        )

    return redirect(url_for("index"))


@app.route("/recommendations", methods=["POST"])
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