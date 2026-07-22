"""
Turns the structured recommendation (from recommend.py) into a plain-language
sentence a shopper actually reads on the product page.

Uses the Gemini API (google-generativeai) if GEMINI_API_KEY is set; otherwise
falls back to a clear, dynamic local template so the product logic keeps
working end-to-end during development and hackathon presentations even
without a key or if the network/API call fails.
"""

import os

PROMPT_TEMPLATE = """You are writing a one or two sentence, friendly, plain-language fit explanation
for a shopper on a fashion e-commerce app. Do not mention statistics jargon like "n=", "cluster ID",
match levels, or internal field names.

Data:
- Match specificity: {level} (matched on: {matched_on} - the more specific, the more this reflects
  people exactly like the shopper, in this exact brand and item type)
- Shopper's body type group: {cluster_label}
- Brand: {brand}, Category: {category}
- Recommended size: {recommended_size}
- Kept rate: {kept_rate} (fraction of similar buyers who kept the item, i.e. it fit well)
- Common return reason (if any): {common_return_reason}
- Fallback note (if this is a broader, less specific match): {note}

Write the explanation now, in plain English, 1-2 sentences, friendly tone. Mention the brand and
the recommended size by name since that's what the shopper is actually deciding about. If a body
type group is given, you can reference it naturally (e.g. "shoppers with a similar build"), never
the raw label. If matched_on doesn't include "category", make clear this reflects the brand
generally, not this specific item type. If there's a fallback note, be transparent that this is a
general pattern, not personalized to their exact body type yet - but stay encouraging, not apologetic.
"""


def build_prompt(brand: str, category: str, result: dict) -> str:
    stats = result["stats"]
    return PROMPT_TEMPLATE.format(
        level=result["level"],
        matched_on=", ".join(result["matched_on"]) or "no strong match",
        cluster_label=stats.get("cluster_label") or "not applicable at this match level",
        brand=brand,
        category=category,
        recommended_size=stats.get("recommended_size") or "not available",
        kept_rate=stats.get("kept_rate"),
        common_return_reason=stats.get("common_return_reason") or "none reported",
        note=result.get("note", "none"),
    )


def _local_fallback_sentence(result: dict, brand: str) -> str:
    """Dynamic, user-facing fallback sentence - used whenever no API key is set,
    or if the live API call fails for any reason (network issue, bad credentials,
    rate limit, etc). Never crashes the /fit-twin endpoint, and never shows a
    developer-only placeholder string to an end user during a demo."""
    stats = result.get("stats", {})
    kept_rate = stats.get("kept_rate")
    kept_pct = int(round(kept_rate * 100)) if kept_rate is not None else None
    size = stats.get("recommended_size") or "your usual size"

    if result.get("level") == "global_fallback":
        pct_text = f"{kept_pct}% of the time" if kept_pct is not None else "consistently"
        return (
            f"We don't have enough data on {brand} for your exact body type yet, but shoppers "
            f"generally kept size {size} in this category {pct_text} — a solid starting point."
        )

    cluster_label = stats.get("cluster_label")
    who = f"shoppers with a similar build ({cluster_label})" if cluster_label else "similar shoppers"
    pct_text = f"{kept_pct}% of" if kept_pct is not None else "most"
    return f"{pct_text} {who} who bought {brand} kept size {size} — worth trying true to size."


def call_llm(prompt: str, result: dict = None, brand: str = None) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    fallback_available = result is not None and brand is not None

    if not api_key:
        if fallback_available:
            return _local_fallback_sentence(result, brand)
        return "Based on similar shoppers' outcomes, this size is likely to fit well."

    try:
        import google.generativeai as genai  # pip install google-generativeai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        text = (response.text or "").strip()
        if text:
            return text
        # empty response from the API - fall through to local fallback
        raise ValueError("Empty response from Gemini")
    except Exception:
        # network issue, bad/missing credential, rate limit, or any other API
        # failure should never take down the /fit-twin endpoint during a demo
        if fallback_available:
            return _local_fallback_sentence(result, brand)
        return "Based on similar shoppers' outcomes, this size is likely to fit well."


if __name__ == "__main__":
    from recommend import get_recommendation

    # specific match case
    result = get_recommendation(height_cm=162, weight_kg=60, gender="Female", brand="Biba", category="Kurti")
    prompt = build_prompt("Biba", "Kurti", result)
    print(call_llm(prompt, result=result, brand="Biba"))

    # force a thin/unlikely combo to see the fallback explanation path
    result2 = get_recommendation(height_cm=150, weight_kg=45, gender="Male", brand="W", category="Dress")
    prompt2 = build_prompt("W", "Dress", result2)
    print(call_llm(prompt2, result=result2, brand="W"))
