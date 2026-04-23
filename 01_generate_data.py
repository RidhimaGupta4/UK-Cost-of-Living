"""
UK Cost-of-Living Dashboard — Data Generation Script
=====================================================
This script generates realistic, ONS/CPI-aligned data for all UK regions.
In a live project, replace the synthetic generators with direct ONS API calls
(see fetch_ons_data() stub at the bottom).

Data sources referenced:
  - ONS CPI: https://www.ons.gov.uk/economy/inflationandpriceindices
  - ONS ASHE (wages): https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours
  - ONS Housing: https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/housepriceindex
  - ONS Regional GDP: https://www.ons.gov.uk/economy/grossdomesticproductgdp

Run:
    pip install pandas numpy
    python 01_generate_data.py
"""

import pandas as pd
import numpy as np
import json
import os

np.random.seed(42)

# ── Constants ────────────────────────────────────────────────────────────────

REGIONS = [
    "London", "South East", "East of England", "South West",
    "East Midlands", "West Midlands", "Yorkshire and The Humber",
    "North West", "North East", "Wales", "Scotland", "Northern Ireland"
]

YEARS = list(range(2018, 2025))

# Base median annual wages (£) by region — ONS ASHE 2023 aligned
BASE_WAGES = {
    "London": 41_000,
    "South East": 34_500,
    "East of England": 32_000,
    "South West": 29_500,
    "East Midlands": 28_000,
    "West Midlands": 28_500,
    "Yorkshire and The Humber": 27_500,
    "North West": 29_000,
    "North East": 26_500,
    "Wales": 26_000,
    "Scotland": 30_000,
    "Northern Ireland": 26_500,
}

# Average monthly rent (£) by region — Rightmove/ONS aligned
BASE_RENT = {
    "London": 2_100,
    "South East": 1_250,
    "East of England": 1_050,
    "South West": 950,
    "East Midlands": 750,
    "West Midlands": 780,
    "Yorkshire and The Humber": 720,
    "North West": 800,
    "North East": 620,
    "Wales": 650,
    "Scotland": 850,
    "Northern Ireland": 680,
}

# Average house price (£) by region — Land Registry aligned
BASE_HOUSE_PRICE = {
    "London": 510_000,
    "South East": 375_000,
    "East of England": 320_000,
    "South West": 290_000,
    "East Midlands": 220_000,
    "West Midlands": 230_000,
    "Yorkshire and The Humber": 195_000,
    "North West": 210_000,
    "North East": 155_000,
    "Wales": 190_000,
    "Scotland": 185_000,
    "Northern Ireland": 170_000,
}

# Monthly grocery basket (£) — ONS CPI basket aligned
BASE_GROCERY = {
    "London": 420,
    "South East": 390,
    "East of England": 370,
    "South West": 360,
    "East Midlands": 340,
    "West Midlands": 345,
    "Yorkshire and The Humber": 335,
    "North West": 340,
    "North East": 325,
    "Wales": 330,
    "Scotland": 345,
    "Northern Ireland": 320,
}

# CPI inflation rates by year (UK headline, ONS-aligned)
CPI_RATES = {
    2018: 2.4,
    2019: 1.8,
    2020: 0.9,
    2021: 2.6,
    2022: 9.1,
    2023: 7.3,
    2024: 3.2,
}

# ── Data Builders ─────────────────────────────────────────────────────────────

def build_wages_df():
    rows = []
    for region in REGIONS:
        base = BASE_WAGES[region]
        for year in YEARS:
            growth = CPI_RATES[year] / 100
            # wages lag inflation in 2022–2023, recover in 2024
            if year == 2022:
                growth *= 0.65
            elif year == 2023:
                growth *= 0.75
            elif year == 2024:
                growth *= 1.10
            noise = np.random.uniform(-0.005, 0.005)
            base = base * (1 + growth + noise)
            rows.append({
                "region": region,
                "year": year,
                "median_annual_wage_gbp": round(base, 2),
            })
    return pd.DataFrame(rows)


def build_rent_df():
    rows = []
    for region in REGIONS:
        base = BASE_RENT[region]
        for year in YEARS:
            # Rents accelerated post-2020
            if year <= 2020:
                growth = 0.025 + np.random.uniform(-0.005, 0.005)
            elif year == 2021:
                growth = 0.04 + np.random.uniform(-0.005, 0.005)
            elif year == 2022:
                growth = 0.12 + np.random.uniform(-0.01, 0.01)
            elif year == 2023:
                growth = 0.10 + np.random.uniform(-0.01, 0.01)
            else:
                growth = 0.06 + np.random.uniform(-0.005, 0.005)
            base = base * (1 + growth)
            rows.append({
                "region": region,
                "year": year,
                "avg_monthly_rent_gbp": round(base, 2),
            })
    return pd.DataFrame(rows)


def build_house_price_df():
    rows = []
    for region in REGIONS:
        base = BASE_HOUSE_PRICE[region]
        for year in YEARS:
            if year <= 2020:
                growth = 0.03 + np.random.uniform(-0.01, 0.01)
            elif year == 2021:
                growth = 0.10 + np.random.uniform(-0.01, 0.01)
            elif year == 2022:
                growth = 0.08 + np.random.uniform(-0.01, 0.01)
            elif year == 2023:
                growth = -0.02 + np.random.uniform(-0.01, 0.01)
            else:
                growth = 0.01 + np.random.uniform(-0.005, 0.005)
            base = base * (1 + growth)
            rows.append({
                "region": region,
                "year": year,
                "avg_house_price_gbp": round(base, 2),
            })
    return pd.DataFrame(rows)


def build_grocery_df():
    rows = []
    for region in REGIONS:
        base = BASE_GROCERY[region]
        for year in YEARS:
            rate = CPI_RATES[year] / 100
            noise = np.random.uniform(-0.005, 0.005)
            base = base * (1 + rate + noise)
            rows.append({
                "region": region,
                "year": year,
                "monthly_grocery_gbp": round(base, 2),
            })
    return pd.DataFrame(rows)


def build_cpi_df():
    rows = []
    categories = ["Food & Drink", "Housing & Utilities", "Transport", "Clothing", "Recreation", "Health"]
    # Category weights in the CPI basket (ONS-aligned)
    weights = [0.17, 0.28, 0.15, 0.05, 0.13, 0.06]
    base_indices = {cat: 100 for cat in categories}

    for year in YEARS:
        headline = CPI_RATES[year] / 100
        for cat, w in zip(categories, weights):
            # Food & Housing spike more in 2022–2023
            if cat in ["Food & Drink", "Housing & Utilities"] and year in [2022, 2023]:
                factor = headline * np.random.uniform(1.2, 1.5)
            elif cat == "Transport" and year in [2022, 2023]:
                factor = headline * np.random.uniform(1.1, 1.3)
            else:
                factor = headline * np.random.uniform(0.7, 1.0)
            base_indices[cat] = base_indices[cat] * (1 + factor)
            rows.append({
                "year": year,
                "category": cat,
                "weight": w,
                "cpi_index": round(base_indices[cat], 2),
                "yoy_change_pct": round(factor * 100, 2),
            })
    return pd.DataFrame(rows)


def build_affordability_df(wages_df, rent_df, grocery_df):
    """
    Affordability Index = (Monthly take-home - Essential costs) / Monthly take-home * 100
    Essential costs = Rent + Groceries + estimated transport (£150 flat)
    Lower index = worse affordability
    """
    merged = wages_df.merge(rent_df, on=["region", "year"])
    merged = merged.merge(grocery_df, on=["region", "year"])

    merged["monthly_take_home"] = (merged["median_annual_wage_gbp"] * 0.72) / 12  # ~28% tax+NI
    merged["transport_estimate"] = 150
    merged["total_essential_costs"] = (
        merged["avg_monthly_rent_gbp"] +
        merged["monthly_grocery_gbp"] +
        merged["transport_estimate"]
    )
    merged["disposable_income"] = merged["monthly_take_home"] - merged["total_essential_costs"]
    merged["affordability_index"] = (
        merged["disposable_income"] / merged["monthly_take_home"] * 100
    ).round(1)
    merged["rent_to_income_pct"] = (
        merged["avg_monthly_rent_gbp"] / merged["monthly_take_home"] * 100
    ).round(1)
    merged["house_price_to_income_ratio"] = None  # filled below

    return merged


def build_master_df(wages_df, rent_df, house_price_df, grocery_df):
    aff = build_affordability_df(wages_df, rent_df, grocery_df)
    master = aff.merge(house_price_df, on=["region", "year"])
    annual_take_home = master["median_annual_wage_gbp"] * 0.72
    master["house_price_to_income_ratio"] = (
        master["avg_house_price_gbp"] / annual_take_home
    ).round(2)
    return master


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    out = "/home/claude/uk-cost-of-living/data/processed"
    os.makedirs(out, exist_ok=True)

    print("Generating wages data...")
    wages_df = build_wages_df()
    wages_df.to_csv(f"{out}/wages.csv", index=False)

    print("Generating rent data...")
    rent_df = build_rent_df()
    rent_df.to_csv(f"{out}/rent.csv", index=False)

    print("Generating house price data...")
    house_price_df = build_house_price_df()
    house_price_df.to_csv(f"{out}/house_prices.csv", index=False)

    print("Generating grocery/CPI data...")
    grocery_df = build_grocery_df()
    grocery_df.to_csv(f"{out}/grocery.csv", index=False)

    cpi_df = build_cpi_df()
    cpi_df.to_csv(f"{out}/cpi_categories.csv", index=False)

    print("Building master dataset...")
    master_df = build_master_df(wages_df, rent_df, house_price_df, grocery_df)
    master_df.to_csv(f"{out}/master.csv", index=False)

    # Also export JSON for the dashboard
    master_json = master_df.to_dict(orient="records")
    cpi_json = cpi_df.to_dict(orient="records")

    with open(f"{out}/master.json", "w") as f:
        json.dump(master_json, f, indent=2)
    with open(f"{out}/cpi.json", "w") as f:
        json.dump(cpi_json, f, indent=2)

    print(f"\nAll files saved to {out}/")
    print(f"Master dataset shape: {master_df.shape}")
    print(master_df[master_df["year"] == 2024][
        ["region", "median_annual_wage_gbp", "avg_monthly_rent_gbp",
         "affordability_index", "house_price_to_income_ratio"]
    ].sort_values("affordability_index").to_string(index=False))


# ── ONS API Stub (for production use) ─────────────────────────────────────────

def fetch_ons_data(dataset_id: str, time_filter: str = "2018,2019,2020,2021,2022,2023,2024"):
    """
    Stub for fetching real ONS data via their API.

    Usage:
        df = fetch_ons_data("MM23")  # CPI dataset
        df = fetch_ons_data("EARN01")  # ASHE earnings

    ONS API docs: https://developer.ons.gov.uk/
    """
    import urllib.request
    url = f"https://api.ons.gov.uk/v1/dataset/{dataset_id}/timeseries/D7BT/data"
    # Replace D7BT with the correct series ID for your metric
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())
        return pd.DataFrame(data.get("years", []))
    except Exception as e:
        print(f"ONS API fetch failed: {e}")
        return pd.DataFrame()


if __name__ == "__main__":
    main()
