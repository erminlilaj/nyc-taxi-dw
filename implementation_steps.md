# Implementation Steps — NYC Taxi Data Warehouse

**Course:** DM2526 — Data Management 2025/2026
**Dataset:** NYC TLC Yellow Taxi Trip Records (Jan–Mar 2024)
**Stack:** PostgreSQL 16 (Docker) · Python 3.10+ · pandas · SQLAlchemy · matplotlib/seaborn

Status flags: `[ done ]` `[ in progress ]` `[ pending ]` `[ blocked ]`

---

## Phase 1 — Project Setup

| # | Step | Status |
|---|------|--------|
| 1.1 | Initialise git repository | `[ done ]` |
| 1.2 | Create `.gitignore` (data, output, venv, agent files) | `[ done ]` |
| 1.3 | Write `implementation_steps.md` (this file) | `[ done ]` |
| 1.4 | Create Python virtual environment, install dependencies, generate `requirements.txt` | `[ done ]` |
| 1.5 | Write `docker-compose.yml` (PostgreSQL 16 + Adminer) | `[ done ]` |
| 1.6 | Verify Docker services start and DB is reachable | `[ done ]` |
| 1.7 | Write `README.md` with setup instructions | `[ done ]` |

---

## Phase 2 — Data Acquisition

| # | Step | Status |
|---|------|--------|
| 2.1 | Write `etl/download.py` to fetch the 3 Parquet files and `zones.csv` | `[ done ]` |
| 2.2 | Run `download.py` and verify all 4 files land in `data/raw/` | `[ done ]` |
| 2.3 | Spot-check raw row counts (~9–10 M total across 3 months) | `[ done ]` |

---

## Phase 3 — Data Cleaning & Transformation

| # | Step | Status |
|---|------|--------|
| 3.1 | Write `etl/clean.py` applying all cleaning rules (nulls, ranges, trip_duration) | `[ done ]` |
| 3.2 | Run `clean.py` and compare before/after row counts | `[ done ]` |
| 3.3 | Verify cleaned output files are written to `data/clean/` | `[ done ]` |
| 3.4 | Confirm expected row count (~8–9 M rows survive cleaning) | `[ done ]` |

**Cleaning rules summary:**

- Drop rows where `tpep_pickup_datetime`, `tpep_dropoff_datetime`, `PULocationID`, or `DOLocationID` is null
- Keep `trip_distance` between 0 and 200
- Keep `fare_amount` between 0 and 500
- Keep `total_amount` > 0
- Keep `passenger_count` between 1 and 6
- Keep computed `trip_duration` between 1 and 300 minutes
- Fill null `tip_amount` with 0

---

## Phase 4 — Database Schema (DDL)

| # | Step | Status |
|---|------|--------|
| 4.1 | Write `sql/ddl.sql` with all 6 `CREATE TABLE` statements | `[ pending ]` |
| 4.2 | Apply DDL: `docker exec -i nyc_taxi_postgres psql -U taxi -d nyc_taxi_dw < sql/ddl.sql` | `[ pending ]` |
| 4.3 | Verify all 6 tables exist with `\dt` in psql | `[ pending ]` |

**Tables to create:**

- `DimTime` — `time_id`, year, quarter, month, day, hour, day_of_week, is_weekend
- `DimPickupLocation` — `location_id`, zone, borough, city
- `DimDropoffLocation` — `location_id`, zone, borough, city
- `DimPayment` — `payment_id`, payment_type, payment_category
- `DimService` — `service_id`, vendor_id, vendor_name, service_type
- `FactTrip` — `trip_id`, `time_id`, `pickup_location_id`, `dropoff_location_id`, `payment_id`, `service_id`, fare_amount, tip_amount, total_amount, trip_distance, passenger_count, trip_duration

---

## Phase 5 — ETL Load

| # | Step | Status |
|---|------|--------|
| 5.1 | Write `etl/load.py` — load all dimensions then FactTrip | `[ pending ]` |
| 5.2 | Load `DimPayment` (6 static rows) | `[ pending ]` |
| 5.3 | Load `DimService` (2 static rows) | `[ pending ]` |
| 5.4 | Load `DimPickupLocation` from `zones.csv` | `[ pending ]` |
| 5.5 | Load `DimDropoffLocation` from `zones.csv` | `[ pending ]` |
| 5.6 | Build and load `DimTime` from pickup timestamps (deduplicated) | `[ pending ]` |
| 5.7 | Load `FactTrip` in chunks of 100,000 rows | `[ pending ]` |
| 5.8 | Verify `SELECT COUNT(*) FROM FactTrip` returns 8,000,000+ | `[ pending ]` |

---

## Phase 6 — OLAP Queries

| # | Query | Operation | Status |
|---|-------|-----------|--------|
| 6.1 | Q1 — trip count rollup: hour → day → month | Rollup | `[ pending ]` |
| 6.2 | Q2 — total revenue by quarter | Rollup | `[ pending ]` |
| 6.3 | Q3 — avg fare drill-down: city → borough → zone | Drill-down | `[ pending ]` |
| 6.4 | Q4 — avg trip duration by borough | Drill-down | `[ pending ]` |
| 6.5 | Q5 — slice: January trips only | Slice | `[ pending ]` |
| 6.6 | Q6 — slice: cash payments only | Slice | `[ pending ]` |
| 6.7 | Q7 — dice: weekday vs weekend demand by hour (include `day_of_week`) | Dice | `[ pending ]` |
| 6.8 | Q8 — dice: trip length category × payment type | Dice | `[ pending ]` |
| 6.9 | Q9 — top 10 pickup zones by trip count | Ranking | `[ pending ]` |
| 6.10 | Q10 — avg tip percentage by payment type | Ranking | `[ pending ]` |
| 6.11 | Q11 — peak hour rank per borough (window function) | Window | `[ pending ]` |
| 6.12 | Q12 — monthly revenue per vendor (window function) | Window | `[ pending ]` |
| 6.13 | Export each query result to `output/result_qN.csv` for charting | — | `[ pending ]` |

All queries go in `sql/olap_queries.sql`.

---

## Phase 7 — Visualizations

| # | Chart file | Description | Source query | Status |
|---|------------|-------------|--------------|--------|
| 7.1 | `01_revenue_by_month.png` | Bar — total revenue Jan/Feb/Mar | Q2 | `[ pending ]` |
| 7.2 | `02_demand_by_hour.png` | Dual line — weekday vs weekend | Q7 | `[ pending ]` |
| 7.3 | `03_top10_zones.png` | Horizontal bar — top 10 pickup zones | Q9 | `[ pending ]` |
| 7.4 | `04_tip_by_payment.png` | Pie — avg tip % by payment type | Q10 | `[ pending ]` |
| 7.5 | `05_duration_by_borough.png` | Bar — avg trip duration by borough | Q4 | `[ pending ]` |
| 7.6 | `06_heatmap_hour_dow.png` | Heatmap — hour × day of week | Q7 | `[ pending ]` |
| 7.7 | Write `viz/charts.py` and run it | — | all | `[ pending ]` |
| 7.8 | Verify 6 PNG files appear in `output/charts/` | — | — | `[ pending ]` |

---

## Phase 8 — Diagrams

| # | Step | Status |
|---|------|--------|
| 8.1 | Draw Dimensional Fact Model (DFM) diagram → `diagrams/dfm.png` | `[ pending ]` |
| 8.2 | Draw Entity-Relationship (ER) diagram → `diagrams/er.png` | `[ pending ]` |

---

## Phase 9 — Report

| # | Step | Status |
|---|------|--------|
| 9.1 | Set up report document in `docs/report/` (LaTeX or Word) | `[ pending ]` |
| 9.2 | Write introduction and dataset description | `[ pending ]` |
| 9.3 | Document the star schema design and DFM | `[ pending ]` |
| 9.4 | Document ETL pipeline and cleaning decisions | `[ pending ]` |
| 9.5 | Include all 12 OLAP queries with explanations | `[ pending ]` |
| 9.6 | Embed the 6 charts with analysis | `[ pending ]` |
| 9.7 | Write conclusions | `[ pending ]` |
| 9.8 | Final proofread and formatting pass | `[ pending ]` |

---

## Phase 10 — Final Verification

| # | Check | Status |
|---|-------|--------|
| 10.1 | `docker compose ps` — both services Up | `[ pending ]` |
| 10.2 | `\dt` in psql — 6 tables listed | `[ pending ]` |
| 10.3 | `SELECT COUNT(*) FROM FactTrip` — 8M+ rows | `[ pending ]` |
| 10.4 | `ls output/charts/` — 6 PNG files present | `[ pending ]` |
| 10.5 | All 12 OLAP queries run without errors | `[ pending ]` |
| 10.6 | Report is complete and diagrams are embedded | `[ pending ]` |
| 10.7 | Git history is clean — no data files, no agent files committed | `[ pending ]` |
