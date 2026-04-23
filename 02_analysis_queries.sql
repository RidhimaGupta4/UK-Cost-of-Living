-- ============================================================
-- UK Cost-of-Living Dashboard — SQL Analysis Queries
-- ============================================================
-- These queries are written for SQLite/DuckDB (can run locally).
-- To use with PostgreSQL, change ROUND() calls to ::NUMERIC casts.
--
-- Load CSVs first (DuckDB example):
--   CREATE TABLE master AS SELECT * FROM read_csv_auto('data/processed/master.csv');
--   CREATE TABLE cpi    AS SELECT * FROM read_csv_auto('data/processed/cpi_categories.csv');
-- ============================================================


-- ── 1. AFFORDABILITY RANKING (Latest Year) ─────────────────────────────────
-- Shows which regions are most/least affordable in 2024
-- Useful for: headline KPI cards, bar chart ranking

SELECT
    region,
    ROUND(median_annual_wage_gbp, 0)          AS annual_wage,
    ROUND(avg_monthly_rent_gbp, 0)            AS monthly_rent,
    ROUND(monthly_grocery_gbp, 0)             AS monthly_grocery,
    ROUND(disposable_income, 0)               AS monthly_disposable,
    affordability_index,
    rent_to_income_pct,
    house_price_to_income_ratio,
    CASE
        WHEN affordability_index >= 20 THEN 'High Affordability'
        WHEN affordability_index >= 10 THEN 'Medium Affordability'
        WHEN affordability_index >= 0  THEN 'Low Affordability'
        ELSE 'Unaffordable'
    END AS affordability_band
FROM master
WHERE year = 2024
ORDER BY affordability_index ASC;


-- ── 2. LONDON VS REST OF UK — YEAR-BY-YEAR COMPARISON ─────────────────────
-- Core narrative: how the gap between London and elsewhere has widened

SELECT
    year,
    ROUND(AVG(CASE WHEN region = 'London' THEN median_annual_wage_gbp END), 0)    AS london_wage,
    ROUND(AVG(CASE WHEN region != 'London' THEN median_annual_wage_gbp END), 0)    AS rest_uk_wage,
    ROUND(AVG(CASE WHEN region = 'London' THEN avg_monthly_rent_gbp END), 0)       AS london_rent,
    ROUND(AVG(CASE WHEN region != 'London' THEN avg_monthly_rent_gbp END), 0)      AS rest_uk_rent,
    ROUND(AVG(CASE WHEN region = 'London' THEN affordability_index END), 1)        AS london_affordability,
    ROUND(AVG(CASE WHEN region != 'London' THEN affordability_index END), 1)       AS rest_uk_affordability,
    ROUND(
        AVG(CASE WHEN region = 'London' THEN avg_monthly_rent_gbp END) -
        AVG(CASE WHEN region != 'London' THEN avg_monthly_rent_gbp END), 0
    ) AS rent_gap_gbp
FROM master
GROUP BY year
ORDER BY year;


-- ── 3. WAGE GROWTH vs INFLATION GAP ────────────────────────────────────────
-- Real-terms wage growth: are workers keeping up with inflation?

WITH base AS (
    SELECT region, median_annual_wage_gbp AS base_wage
    FROM master
    WHERE year = 2018
),
current AS (
    SELECT m.region, m.year, m.median_annual_wage_gbp AS current_wage
    FROM master m
),
cpi_cumulative AS (
    -- Approximate cumulative CPI from 2018 to each year
    SELECT 2018 AS year, 1.000 AS cpi_factor UNION ALL
    SELECT 2019,  1.024 UNION ALL
    SELECT 2020,  1.033 UNION ALL
    SELECT 2021,  1.059 UNION ALL
    SELECT 2022,  1.155 UNION ALL
    SELECT 2023,  1.239 UNION ALL
    SELECT 2024,  1.279
)
SELECT
    c.region,
    c.year,
    ROUND(c.current_wage, 0)                                     AS nominal_wage,
    ROUND(c.current_wage / cc.cpi_factor, 0)                    AS real_wage_2018_prices,
    ROUND(b.base_wage, 0)                                        AS base_wage_2018,
    ROUND((c.current_wage / cc.cpi_factor - b.base_wage) / b.base_wage * 100, 1) AS real_wage_change_pct
FROM current c
JOIN base b ON c.region = b.region
JOIN cpi_cumulative cc ON c.year = cc.year
ORDER BY c.region, c.year;


-- ── 4. HOUSE PRICE TO INCOME RATIO TREND ──────────────────────────────────
-- Key housing affordability metric; benchmark: >8x is considered a crisis

SELECT
    region,
    MAX(CASE WHEN year = 2018 THEN house_price_to_income_ratio END) AS ratio_2018,
    MAX(CASE WHEN year = 2020 THEN house_price_to_income_ratio END) AS ratio_2020,
    MAX(CASE WHEN year = 2022 THEN house_price_to_income_ratio END) AS ratio_2022,
    MAX(CASE WHEN year = 2024 THEN house_price_to_income_ratio END) AS ratio_2024,
    ROUND(
        MAX(CASE WHEN year = 2024 THEN house_price_to_income_ratio END) -
        MAX(CASE WHEN year = 2018 THEN house_price_to_income_ratio END), 2
    ) AS change_since_2018
FROM master
GROUP BY region
ORDER BY ratio_2024 DESC;


-- ── 5. CPI BASKET BREAKDOWN — WHICH CATEGORIES HURT MOST ──────────────────
-- Shows which spending categories drove inflation hardest 2021–2023

SELECT
    category,
    year,
    ROUND(yoy_change_pct, 1) AS annual_inflation_pct,
    ROUND(cpi_index, 1)      AS index_vs_2017_base
FROM cpi
WHERE year >= 2021
ORDER BY year, yoy_change_pct DESC;


-- ── 6. REGIONAL DISPOSABLE INCOME MAP DATA ─────────────────────────────────
-- Monthly disposable income after essential costs — for choropleth

SELECT
    region,
    year,
    ROUND(monthly_take_home, 0)          AS monthly_take_home,
    ROUND(total_essential_costs, 0)      AS total_essential_costs,
    ROUND(disposable_income, 0)          AS monthly_disposable,
    ROUND(rent_to_income_pct, 1)         AS rent_burden_pct
FROM master
WHERE year = 2024
ORDER BY monthly_disposable DESC;


-- ── 7. COST SHOCK ANALYSIS 2021–2023 ──────────────────────────────────────
-- How much did essential costs rise per region over the inflation crisis?

WITH cost_2021 AS (
    SELECT region,
           avg_monthly_rent_gbp + monthly_grocery_gbp + 150 AS essential_2021
    FROM master WHERE year = 2021
),
cost_2023 AS (
    SELECT region,
           avg_monthly_rent_gbp + monthly_grocery_gbp + 150 AS essential_2023
    FROM master WHERE year = 2023
)
SELECT
    a.region,
    ROUND(a.essential_2021, 0)               AS monthly_essentials_2021,
    ROUND(b.essential_2023, 0)               AS monthly_essentials_2023,
    ROUND(b.essential_2023 - a.essential_2021, 0) AS absolute_increase_gbp,
    ROUND((b.essential_2023 - a.essential_2021) / a.essential_2021 * 100, 1) AS pct_increase
FROM cost_2021 a
JOIN cost_2023 b ON a.region = b.region
ORDER BY pct_increase DESC;
