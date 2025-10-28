"""Core recommendation logic for the ecommerce demo application."""
from __future__ import annotations

from dataclasses import dataclass
from difflib import get_close_matches
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

from config import (
    DEFAULT_TOP_N,
    N_NEIGHBORS,
    SIMILARITY_WEIGHT,
    TFIDF_MAX_FEATURES,
    TFIDF_MIN_DF,
    TFIDF_NGRAM_RANGE,
    resolve_data_path,
)


@dataclass
class RecommendationResponse:
    """Container returned by the recommendation service."""

    results: pd.DataFrame
    resolved_name: Optional[str]
    suggestions: Sequence[str]
    message: Optional[str] = None


class ProductRecommender:
    """Content-based recommender that blends similarity and popularity signals."""

    def __init__(self, data_file: Optional[str] = None) -> None:
        data_path = resolve_data_path(data_file or "clean_data.csv")
        self.raw_data = pd.read_csv(data_path)
        self.data = self._prepare_dataframe(self.raw_data.copy())

        if self.data.empty:
            raise ValueError("The training dataset is empty; cannot build recommender.")

        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=TFIDF_NGRAM_RANGE,
            max_features=TFIDF_MAX_FEATURES,
            min_df=TFIDF_MIN_DF,
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(self.data["combined_text"])

        n_neighbors = min(N_NEIGHBORS, len(self.data))
        self.nearest_neighbours = NearestNeighbors(metric="cosine", algorithm="brute", n_neighbors=n_neighbors)
        self.nearest_neighbours.fit(self.tfidf_matrix)

        self._name_to_index = self._build_name_index(self.data["Name"].tolist())

    @staticmethod
    def _prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Clean raw columns and add derived fields required downstream."""

        text_columns = ["Name", "Brand", "Category", "Tags", "Description"]
        for col in text_columns:
            df[col] = df[col].fillna("").astype(str)

        df["normalized_name"] = df["Name"].str.lower().str.strip()
        df["normalized_brand"] = df["Brand"].str.replace(r"[^a-z0-9 ]", " ", regex=True).str.lower()

        df["combined_text"] = (
            df["Name"].str.lower()
            + " "
            + df["normalized_brand"]
            + " "
            + df["Category"].str.lower()
            + " "
            + df["Tags"].str.lower()
            + " "
            + df["Description"].str.lower()
        )

        df["rating_clean"] = df["Rating"].fillna(0).clip(lower=0)
        df["review_count_clean"] = df["ReviewCount"].fillna(0).clip(lower=0)

        rating_component = 0.0
        if df["rating_clean"].max() > 0:
            rating_component = df["rating_clean"] / df["rating_clean"].max()

        review_component = 0.0
        if df["review_count_clean"].max() > 0:
            review_component = np.log1p(df["review_count_clean"]) / np.log1p(df["review_count_clean"].max())

        popularity = (rating_component + review_component) / 2
        df["popularity"] = popularity if isinstance(popularity, pd.Series) else 0.0

        return df.reset_index(drop=True)

    @staticmethod
    def _build_name_index(names: Iterable[str]) -> dict:
        index = {}
        for position, name in enumerate(names):
            normalized = name.lower().strip()
            index.setdefault(normalized, position)
        return index

    def _resolve_name(self, item_name: str) -> Tuple[Optional[int], Sequence[str]]:
        if not item_name:
            return None, []

        normalized = item_name.lower().strip()
        if normalized in self._name_to_index:
            return self._name_to_index[normalized], []

        suggestions = get_close_matches(normalized, list(self._name_to_index.keys()), n=5, cutoff=0.6)
        return None, [self.data.iloc[self._name_to_index[name]]["Name"] for name in suggestions]

    def recommend(self, item_name: str, top_n: int = DEFAULT_TOP_N) -> RecommendationResponse:
        index, suggestions = self._resolve_name(item_name)
        if index is None:
            return RecommendationResponse(
                results=pd.DataFrame(),
                resolved_name=None,
                suggestions=suggestions,
                message="Product not found. Please refine your search query.",
            )

        distances, indices = self.nearest_neighbours.kneighbors(self.tfidf_matrix[index])
        candidates = self.data.iloc[indices[0]].copy()
        candidates["similarity"] = 1 - distances[0]
        candidates = candidates[candidates.index != index]

        candidates["score"] = (
            SIMILARITY_WEIGHT * candidates["similarity"]
            + (1 - SIMILARITY_WEIGHT) * candidates["popularity"]
        )

        candidates = candidates.sort_values("score", ascending=False).head(top_n)
        return RecommendationResponse(
            results=candidates[[
                "Name",
                "Brand",
                "ImageURL",
                "Rating",
                "ReviewCount",
                "similarity",
                "popularity",
                "score",
            ]].reset_index(drop=True),
            resolved_name=self.data.iloc[index]["Name"],
            suggestions=suggestions,
        )

    def search(self, query: str, limit: int = 10) -> List[str]:
        """Return fuzzy-matched product names to drive autocomplete features."""

        normalized_query = query.lower().strip()
        matches = get_close_matches(normalized_query, list(self._name_to_index.keys()), n=limit, cutoff=0.4)
        return [self.data.iloc[self._name_to_index[name]]["Name"] for name in matches]
