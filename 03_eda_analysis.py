"""
UK Cost-of-Living Dashboard — Exploratory Data Analysis
=========================================================
Generates all charts used in the Power BI/Tableau equivalent dashboard.
Outputs PNG files to outputs/ for inclusion in reports or presentations.

Run:
    pip install pandas numpy matplotlib seaborn
    python 03_eda_analysis.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import warnings
import os

warnings.filterwarnings("ignore")

# ── Setup ─────────────────────────────────────────────────────────────────────

DATA = "/home/claude/uk-cost-of-living/data/processed"
OUT  = "/home/claude/uk-cost-of-living/outputs"
os.makedirs(OUT, exist_ok=True)

master = pd.read_csv(f"{DATA}/master.csv")
cpi    = pd.read_csv(f"{DATA}/cpi_categories.csv")

# Colour palette
LONDON_COLOR  = "#E8453C"
UK_COLOR      = "#2563EB"
ACCENT        = "#F59E0B"
MUTED         = "#94A3B8"
BG            = "#F8FAFC"
TEXT          = "#1E293B"

REGION_PALETTE = {
    "London": "#E8453C",
    "South East": "#F97316",
    "East of England": "#F59E0B",
    "South West": "#84CC16",
    "East Midlands": "#10B981",
    "West Midlands": "#06B6D4",
    "Yorkshire and The Humber": "#3B82F6",
    "North West": "#8B5CF6",
    "North East": "#EC4899",
    "Wales": "#14B8A6",
    "Scotland": "#6366F1",
    "Northern Ireland": "#78716C",
}

def style_ax(ax, title="", xlabel="", ylabel=""):
    ax.set_facecolor(BG)
    ax.spines[["top","right"]].set_visible(False)
    ax.spines[["left","bottom"]].set_color("#CBD5E1")
    ax.tick_params(colors=TEXT, labelsize=9)
    if title:
        ax.set_title(title, fontsize=13, fontweight="bold", color=TEXT, pad=12)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=9, color=MUTED)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9, color=MUTED)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))


# ── Chart 1: Affordability Index 2024 ────────────────────────────────────────

def chart_affordability_ranking():
    df = master[master["year"] == 2024].sort_values("affordability_index")
    colors = [LONDON_COLOR if r == "London" else UK_COLOR for r in df["region"]]

    fig, ax = plt.subplots(figsize=(10, 6), facecolor="white")
    bars = ax.barh(df["region"], df["affordability_index"], color=colors, height=0.65)

    for bar, val in zip(bars, df["affordability_index"]):
        label_x = val - 1.5 if val < 0 else val + 0.3
        ha = "right" if val < 0 else "left"
        ax.text(label_x, bar.get_y() + bar.get_height()/2,
                f"{val:.1f}%", va="center", ha=ha, fontsize=9, color=TEXT, fontweight="bold")

    ax.axvline(0, color=TEXT, linewidth=0.8, linestyle="--", alpha=0.4)
    style_ax(ax,
             title="Affordability Index by Region — 2024\n(% of take-home income remaining after rent, food & transport)",
             xlabel="Affordability Index (%)")
    ax.legend(handles=[
        mpatches.Patch(color=LONDON_COLOR, label="London"),
        mpatches.Patch(color=UK_COLOR, label="Rest of UK"),
    ], fontsize=9, framealpha=0)

    plt.tight_layout()
    plt.savefig(f"{OUT}/01_affordability_ranking_2024.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: 01_affordability_ranking_2024.png")


# ── Chart 2: London vs Rest of UK — Rent Over Time ───────────────────────────

def chart_london_vs_rest_rent():
    london = master[master["region"] == "London"].sort_values("year")
    rest   = master[master["region"] != "London"].groupby("year")["avg_monthly_rent_gbp"].mean().reset_index()

    fig, ax = plt.subplots(figsize=(10, 5), facecolor="white")
    ax.plot(london["year"], london["avg_monthly_rent_gbp"], color=LONDON_COLOR,
            linewidth=2.5, marker="o", markersize=6, label="London")
    ax.plot(rest["year"], rest["avg_monthly_rent_gbp"], color=UK_COLOR,
            linewidth=2.5, marker="o", markersize=6, label="Rest of UK (avg)")

    # Shade the gap
    ax.fill_between(london["year"], london["avg_monthly_rent_gbp"],
                    rest["avg_monthly_rent_gbp"], alpha=0.08, color=LONDON_COLOR)

    style_ax(ax, title="Average Monthly Rent: London vs Rest of UK (2018–2024)",
             xlabel="Year", ylabel="Monthly Rent (£)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"£{x:,.0f}"))
    ax.legend(fontsize=10, framealpha=0)
    ax.set_xticks(YEARS := list(range(2018, 2025)))

    plt.tight_layout()
    plt.savefig(f"{OUT}/02_london_vs_rest_rent.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: 02_london_vs_rest_rent.png")


# ── Chart 3: Real Wage Change (inflation-adjusted) ───────────────────────────

def chart_real_wage_change():
    cpi_factors = {2018:1.000, 2019:1.024, 2020:1.033,
                   2021:1.059, 2022:1.155, 2023:1.239, 2024:1.279}

    base_wages = master[master["year"] == 2018].set_index("region")["median_annual_wage_gbp"]
    df24 = master[master["year"] == 2024].copy()
    df24["real_wage"] = df24["median_annual_wage_gbp"] / cpi_factors[2024]
    df24["real_change_pct"] = (df24["real_wage"] - df24["region"].map(base_wages)) / df24["region"].map(base_wages) * 100

    df24 = df24.sort_values("real_change_pct")
    colors = [LONDON_COLOR if r == "London" else (ACCENT if v >= 0 else "#EF4444")
              for r, v in zip(df24["region"], df24["real_change_pct"])]

    fig, ax = plt.subplots(figsize=(10, 6), facecolor="white")
    bars = ax.barh(df24["region"], df24["real_change_pct"], color=colors, height=0.65)
    ax.axvline(0, color=TEXT, linewidth=0.8, linestyle="--", alpha=0.4)

    for bar, val in zip(bars, df24["real_change_pct"]):
        lx = val - 0.3 if val < 0 else val + 0.3
        ha = "right" if val < 0 else "left"
        ax.text(lx, bar.get_y() + bar.get_height()/2,
                f"{val:+.1f}%", va="center", ha=ha, fontsize=9, color=TEXT, fontweight="bold")

    style_ax(ax,
             title="Real Wage Change 2018→2024 (inflation-adjusted, 2018 prices)\nNegative = workers earning less in real terms",
             xlabel="Real Wage Change (%)")
    plt.tight_layout()
    plt.savefig(f"{OUT}/03_real_wage_change.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: 03_real_wage_change.png")


# ── Chart 4: CPI Category Breakdown 2021–2023 ────────────────────────────────

def chart_cpi_breakdown():
    df = cpi[cpi["year"].isin([2021, 2022, 2023])].copy()
    pivot = df.pivot(index="category", columns="year", values="yoy_change_pct")

    fig, ax = plt.subplots(figsize=(10, 5), facecolor="white")
    x = np.arange(len(pivot))
    w = 0.25
    years = [2021, 2022, 2023]
    palette = [UK_COLOR, LONDON_COLOR, ACCENT]

    for i, (yr, col) in enumerate(zip(years, palette)):
        bars = ax.bar(x + i*w, pivot[yr], width=w, color=col, alpha=0.9, label=str(yr))

    ax.set_xticks(x + w)
    ax.set_xticklabels(pivot.index, rotation=20, ha="right", fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.1f}%"))
    style_ax(ax,
             title="CPI Inflation by Category — The Cost-of-Living Crisis (2021–2023)",
             ylabel="Annual % Inflation")
    ax.legend(fontsize=9, framealpha=0)

    plt.tight_layout()
    plt.savefig(f"{OUT}/04_cpi_breakdown.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: 04_cpi_breakdown.png")


# ── Chart 5: House Price to Income Ratio ─────────────────────────────────────

def chart_house_price_income():
    focus = ["London", "South East", "North East", "Scotland", "Yorkshire and The Humber", "Wales"]
    df = master[master["region"].isin(focus)].sort_values("year")

    fig, ax = plt.subplots(figsize=(10, 5), facecolor="white")
    for region in focus:
        sub = df[df["region"] == region]
        col = REGION_PALETTE.get(region, MUTED)
        lw = 2.8 if region == "London" else 1.8
        ax.plot(sub["year"], sub["house_price_to_income_ratio"],
                color=col, linewidth=lw, marker="o", markersize=4, label=region)

    ax.axhline(8, color=TEXT, linewidth=0.8, linestyle=":", alpha=0.5)
    ax.text(2023.9, 8.2, "Crisis threshold (8x)", fontsize=8, color=MUTED)

    style_ax(ax,
             title="House Price-to-Income Ratio (2018–2024)\nHow many years of full salary to buy an average home",
             xlabel="Year", ylabel="Ratio (×)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}×"))
    ax.set_xticks(list(range(2018, 2025)))
    ax.legend(fontsize=9, framealpha=0, ncol=2)

    plt.tight_layout()
    plt.savefig(f"{OUT}/05_house_price_income_ratio.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: 05_house_price_income_ratio.png")


# ── Chart 6: Cost Shock 2021–2023 ────────────────────────────────────────────

def chart_cost_shock():
    c21 = master[master["year"] == 2021].set_index("region")
    c23 = master[master["year"] == 2023].set_index("region")

    shock = pd.DataFrame({
        "region": master["region"].unique(),
    }).set_index("region")

    shock["essentials_2021"] = c21["avg_monthly_rent_gbp"] + c21["monthly_grocery_gbp"] + 150
    shock["essentials_2023"] = c23["avg_monthly_rent_gbp"] + c23["monthly_grocery_gbp"] + 150
    shock["increase"] = shock["essentials_2023"] - shock["essentials_2021"]
    shock = shock.sort_values("increase", ascending=False).reset_index()

    fig, ax = plt.subplots(figsize=(10, 6), facecolor="white")
    bars = ax.barh(shock["region"], shock["increase"],
                   color=[LONDON_COLOR if r == "London" else ACCENT for r in shock["region"]],
                   height=0.65)

    for bar, val in zip(bars, shock["increase"]):
        ax.text(val + 5, bar.get_y() + bar.get_height()/2,
                f"+£{val:,.0f}/mo", va="center", fontsize=9, color=TEXT, fontweight="bold")

    style_ax(ax,
             title="Monthly Essential Cost Increase: 2021 → 2023\n(Rent + Groceries + Transport)",
             xlabel="Monthly Increase (£)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"£{x:,.0f}"))

    plt.tight_layout()
    plt.savefig(f"{OUT}/06_cost_shock_2021_2023.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: 06_cost_shock_2021_2023.png")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating analysis charts...\n")
    chart_affordability_ranking()
    chart_london_vs_rest_rent()
    chart_real_wage_change()
    chart_cpi_breakdown()
    chart_house_price_income()
    chart_cost_shock()
    print(f"\nAll charts saved to {OUT}/")
