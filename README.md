# Retention Analytics Dashboard — European Central Bank

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
Make sure `European_Bank.csv` is in the same folder as `app.py`.

## What's inside
- **Engagement vs Churn** — active/inactive churn comparison, engagement profile mix by geography
- **Product Utilization Impact** — churn by product count, single vs multi-product retention
- **High-Value Disengaged Detector** — adjustable balance/salary percentile thresholds to surface "silent churn" premium customers
- **Retention Strength Scoring** — composite Relationship Strength Index (0–100) and churn by tier

## KPIs on the dashboard
- Engagement Retention Ratio
- Product Depth Index
- High-Balance Disengagement Rate
- Credit Card Stickiness Score
- Relationship Strength Index

## Sidebar filters
Geography, Gender, Engagement Profile, Number of Products, Balance range, Salary range, Age range.
