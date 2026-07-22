# MynFit

MynFit is a fashion fit-recommendation demo. It recommends a clothing size
from a shopper's height, weight, gender, product brand, and category. The
recommendation is based on similar shoppers' fit outcomes in the supplied
20,000-row dataset.

## Features

- Product browsing and product-detail screens
- Fit form for height, weight, and gender
- Size recommendation API powered by FastAPI
- Gender-specific body clusters built from height and weight
- Confidence and fit explanation based on comparable shoppers
- Shared browser state for the selected product, shopper profile, and size

## Project structure

```text
backend/                         FastAPI recommendation service
  app.py                          API entry point
  recommend.py                    Recommendation and fallback logic
  clustering.py                   Gender-specific KMeans clustering
  fit_stats.py                    Fit statistics and size scoring
  data/                           Dataset and cleaned data

frontend-stitch/                 Static HTML frontend
  mynfit_landing_page/            First page to open
  mynfit_product_listing_page/    Product listing
  mynfit_product_detail_page/     Blazer detail page
  mynfit_recommendation_flow/     Measurement and recommendation flow
  shared/mynfit.js                Shared API and browser-state helper
```

## Requirements

- Python 3.11 or later
- The included Python environment at `backend/venv` or the dependencies in
  `backend/requirements.txt`
- A modern browser such as Chrome or Edge

## Run the project locally

### 1. Start the backend

Open PowerShell in the project folder and run:

```powershell
cd backend
.\venv\Scripts\python.exe -m uvicorn app:app --reload
```

The API runs at `http://127.0.0.1:8000`.

You can confirm that it is working by opening:

```text
http://127.0.0.1:8000/docs
```

Keep this PowerShell window open while using the frontend.

### 2. Open the frontend

Open this file in your browser:

```text
frontend-stitch/mynfit_landing_page/code.html
```

This is the project’s first page. From there, browse products or select
**Find Your Fit**.

### 3. Use the fit recommendation

1. Select a product or choose **Find Your Fit**.
2. Enter height, weight, and gender.
3. Select **Calculate Recommendation**.
4. The frontend sends a request to `POST /fit-twin` and displays the
   recommended size.

## API

### `POST /fit-twin`

Example request body:

```json
{
  "height_cm": 165,
  "weight_kg": 62,
  "gender": "Female",
  "brand": "Zara",
  "category": "Shirt"
}
```

The response includes the recommended size, confidence information, matching
level, cohort statistics, and a shopper-friendly explanation.

## Recommendation approach

MynFit first finds a gender-specific height/weight cluster, then looks for
enough comparable shoppers using this order:

1. Cluster + brand + category
2. Cluster + category
3. Cluster + brand
4. Cluster only
5. Brand + category
6. Category only
7. Brand only
8. Overall dataset baseline

A size must have at least 10 matching shopper records before it can be
recommended. This prevents very small groups from producing unreliable size
recommendations.

## Troubleshooting

- **“Could not reach the Fit Twin backend”**: ensure the backend command is
  still running and that port `8000` is available.
- **Old recommendations after changing backend code**: stop the running API
  with `Ctrl+C`, then start it again using the command above.
- **Frontend is deployed separately**: set `window.MYNFIT_API_BASE_URL` before
  loading `frontend-stitch/shared/mynfit.js` so it points to the deployed API.

## Current scope

This is a demo application. Product data, cart actions, wishlist, filters, and
most navigation are frontend prototypes. The fit recommendation flow is the
connected backend feature.
