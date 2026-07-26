"""
MynFit backend API.

Run with: uvicorn app:app --reload
Then open: http://127.0.0.1:8000/docs to try the /mynfit endpoint interactively.
"""

import os
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ensures recommend.py / genai_explain.py are importable regardless of the
# working directory this app is launched from
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from recommend import get_recommendation
from genai_explain import build_prompt, call_llm

app = FastAPI(title="MynFit API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # fine for hackathon demo; restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)


class MynFitRequest(BaseModel):
    height_cm: float
    weight_kg: float
    gender: str    # "Male" or "Female" (anything else safely falls back to the pooled cluster model)
    brand: str     # e.g. "Roadster", "Zara", "Biba", "Nike" ...
    category: str  # e.g. "Kurti", "Jeans", "Shirt", "Dress", "Trousers", "Top"


@app.post("/mynfit")
def mynfit(req: MynFitRequest):
    if req.height_cm <= 0 or req.weight_kg <= 0:
        raise HTTPException(status_code=400, detail="height_cm and weight_kg must be positive numbers.")
    if not req.brand or not req.category:
        raise HTTPException(status_code=400, detail="brand and category are required.")

    try:
        result = get_recommendation(req.height_cm, req.weight_kg, req.gender, req.brand, req.category)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not compute a recommendation: {e}")

    stats = result.get("stats", {}) or {}

    try:
        prompt = build_prompt(req.brand, req.category, result)
        explanation = call_llm(prompt, result=result, brand=req.brand)
    except Exception:
        # even if the explanation layer fails entirely, the numeric recommendation
        # should still reach the frontend rather than a 500
        explanation = "Based on similar shoppers' outcomes, this size is likely to fit well."

    return {
        "match_specificity": result.get("level"),
        "matched_on": result.get("matched_on", []),
        "cluster": result.get("cluster"),
        "cluster_label": stats.get("cluster_label"),
        "recommended_size": result.get("recommended_size"),
        "confidence_score": result.get("confidence_score"),
        "stats": stats,
        "reviews": result.get("reviews", []),
        "explanation": explanation,
    }


@app.get("/")
def root():
    return {"status": "MynFit API running. POST to /mynfit with height_cm, weight_kg, gender, brand, category."}
