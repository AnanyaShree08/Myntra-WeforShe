"""
One-time (or whenever you get updated data) prep script for MynFit.
Run: python data_prep.py

What it does:
1. Loads the real FitTwin dataset
2. Fits the body clusterer (clustering.py - KMeans per gender, with a pooled
   fallback model) and saves it to cluster_model.pkl so recommend.py can load
   it later without refitting
3. Assigns every row its body cluster (already gender-specific, e.g.
   "Female_Cluster_2" - no separate gender column needed downstream)
4. Standardizes outcome (kept/returned) and reason fields
5. Saves the cleaned CSV that fit_stats.py / recommend.py read from
6. Prints real coverage stats so you know, before building anything else,
   how many (cluster, brand, category) combinations have enough data points
   to show a personalized result vs. need to fall back
"""

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clustering import fit_and_save

_HERE = os.path.dirname(os.path.abspath(__file__))
RAW_PATH = os.path.join(_HERE, "data", "FitTwin_Realistic_Dataset_20000.xlsx")
CLEAN_PATH = os.path.join(_HERE, "data", "clean_fit_data.csv")
MIN_DATA_POINTS = 15  # matches the threshold used in recommend.py's fallback ladder


def main():
    df = pd.read_excel(RAW_PATH)

    # fit the body clusterer on this dataset and save it for reuse at request time
    clusterer = fit_and_save(df)
    print(f"Cluster model fit and saved ({len(clusterer.cluster_labels)} labeled clusters).")

    df = clusterer.assign_clusters_to_df(df)

    # standardize outcome: Kept -> good signal, Returned -> bad signal
    df["outcome"] = df["kept_or_returned"].map({"Kept": "kept", "Returned": "returned"})

    # reason only meaningful for returned rows
    df["reason"] = df.apply(
        lambda r: r["return_reason"] if r["outcome"] == "returned" else None, axis=1
    )

    keep_cols = [
        "user_id", "gender", "height_cm", "weight_kg", "cluster",
        "brand", "category", "product_name",
        "size_bought", "outcome", "reason",
        "fit_feedback", "rating", "review", "purchase_date",
    ]
    clean = df[keep_cols]
    clean.to_csv(CLEAN_PATH, index=False)
    print(f"Saved cleaned data to {CLEAN_PATH} - {len(clean)} rows")

    # coverage check at each level of the fallback ladder recommend.py uses
    # (gender is already baked into `cluster`, so it's not a separate key here)
    print("\n--- Coverage check (how often each ladder level has enough real data) ---")
    levels = [
        ("cluster + brand + category (most specific)", ["cluster", "brand", "category"]),
        ("cluster + brand", ["cluster", "brand"]),
        ("brand only", ["brand"]),
        ("category only (last resort)", ["category"]),
    ]
    for name, keys in levels:
        g = clean.groupby(keys).size().reset_index(name="n")
        usable = (g["n"] >= MIN_DATA_POINTS).sum()
        print(f"{name:45s} | combos: {len(g):4d} | usable (15+): {usable:4d} ({100*usable/len(g):.0f}%) | median n: {g['n'].median()}")

    print("\n--- Sample cluster labels (for reference in the demo/pitch) ---")
    for cluster_id, label in clusterer.cluster_labels.items():
        print(f"  {cluster_id:20s} -> {label}")


if __name__ == "__main__":
    main()
