"""
Core MynFit recommendation logic - cascading fallback ladder.

Tries the most specific, brand-aware match first, and only drops to a
broader level if there isn't enough real data to trust it. This keeps
brand-specific sizing signal (what actually matters to a shopper browsing
a specific brand) for as long as the data can support it.

Ladder, most specific -> least specific.  The first four levels preserve the
shopper's body cluster; broad brand/category averages are only used when there
is not enough comparable-body data.

Gender is not a separate ladder key - it's already baked into `cluster`
(see clustering.py), so every level above is implicitly gender-aware.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from clustering import assign_cluster
from fit_stats import (
    load_clean,
    compute_cluster_brand_category_stats,
    compute_cluster_brand_stats,
    compute_cluster_category_stats,
    compute_cluster_stats,
    compute_brand_category_stats,
    compute_brand_stats,
    compute_category_stats,
    compute_global_stats,
    get_similar_reviews,
)

MIN_DATA_POINTS = 15  # tuned against the real 20,000-row dataset - see data_prep.py output


def _is_usable(stats: dict) -> bool:
    """A cohort needs both enough shoppers and an adequately supported size."""
    return stats.get("n", 0) >= MIN_DATA_POINTS and bool(stats.get("recommended_size"))


def _confidence_score(kept_rate: float, n: int) -> float:
    """Statistical confidence score that penalizes low-sample cohorts, so a
    matched group with only a handful of data points doesn't score as
    confidently as one backed by real volume, even at the same kept_rate.

    confidence = (kept_rate * 100) * (0.8 + 0.2 * (n / 50))

    A cohort with n=50+ gets the full multiplier (up to 1.0x); a thinner
    cohort gets scaled down toward 0.8x. Capped at 100.
    """
    if kept_rate is None or n == 0:
        return 0.0
    raw = (kept_rate * 100.0) * (0.8 + 0.2 * (n / 50.0))
    return round(min(raw, 100.0), 1)


def _build_result(
    level: str,
    cluster: str,
    matched_on: list,
    stats: dict,
    df,
    height_cm: float,
    weight_kg: float,
    brand: str,
    category: str,
    note: str = None,
) -> dict:
    recommended_size = stats.get("recommended_size")

    result = {
        "level": level,
        "cluster": cluster,
        "matched_on": matched_on,
        "recommended_size": recommended_size,
        "confidence_score": _confidence_score(stats.get("kept_rate"), stats.get("n", 0)),
        "stats": stats,
        "reviews": get_similar_reviews(
            df,
            cluster,
            brand,
            category,
            recommended_size,
            height_cm,
            weight_kg,
        ),
    }
    if note:
        result["note"] = note
    return result


def get_recommendation(height_cm: float, weight_kg: float, gender: str, brand: str, category: str,
                        csv_path: str = None) -> dict:
    df = load_clean(csv_path)
    cluster = assign_cluster(gender, height_cm, weight_kg)

    # Level 1: exact comparable shoppers and exact item context.
    stats = compute_cluster_brand_category_stats(df, cluster, brand, category)
    if _is_usable(stats):
        return _build_result("cluster_brand_category", cluster, ["cluster", "brand", "category"], stats, df, height_cm, weight_kg, brand, category)

    # Prefer an equivalent item category for the same body cluster before
    # broadening to brand-level behaviour.
    stats = compute_cluster_category_stats(df, cluster, category)
    if _is_usable(stats):
        return _build_result("cluster_category", cluster, ["cluster", "category"], stats, df, height_cm, weight_kg, brand, category)

    stats = compute_cluster_brand_stats(df, cluster, brand)
    if _is_usable(stats):
        return _build_result("cluster_brand", cluster, ["cluster", "brand"], stats, df, height_cm, weight_kg, brand, category)

    stats = compute_cluster_stats(df, cluster)
    if _is_usable(stats):
        return _build_result("cluster_only", cluster, ["cluster"], stats, df, height_cm, weight_kg, brand, category)

    # These levels are general sizing patterns, not personalized predictions.
    stats = compute_brand_category_stats(df, brand, category)
    if _is_usable(stats):
        return _build_result("brand_category", cluster, ["brand", "category"], stats, df, height_cm, weight_kg, brand, category)

    stats = compute_category_stats(df, category)
    if _is_usable(stats):
        return _build_result("category_only", cluster, ["category"], stats, df, height_cm, weight_kg, brand, category)

    # Keep a brand-only result below category-only: it cannot infer a garment
    # silhouette and is therefore the weaker broad fallback.
    stats = compute_brand_stats(df, brand)
    if _is_usable(stats):
        return _build_result("brand_only", cluster, ["brand"], stats, df, height_cm, weight_kg, brand, category)

    stats = compute_global_stats(df)
    note = f"Not enough comparable shopper data is available for {brand} {category}; showing the overall size pattern."
    return _build_result("global_fallback", cluster, [], stats, df, height_cm, weight_kg, brand, category, note=note)


if __name__ == "__main__":
    result = get_recommendation(height_cm=162, weight_kg=60, gender="Female", brand="Biba", category="Kurti")
    print(result)

    result2 = get_recommendation(height_cm=178, weight_kg=88, gender="Male", brand="Nike", category="Dress")
    print(result2)
