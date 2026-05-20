# NYC Taxi Data Warehouse

**Course:** DM2526 — Data Management 2025/2026
**Dataset:** NYC TLC Yellow Taxi Trip Records — January, February, March 2024
**Stack:** PostgreSQL 16 · Python 3.10+ · pandas · SQLAlchemy · matplotlib/seaborn

A data warehouse project in progress. Setup, data acquisition, cleaning, PostgreSQL schema creation, warehouse loading, and OLAP query exports are complete; visualizations, diagrams, and the report are the next phases.

---

## Dataset Statistics

### Raw data (downloaded)

| File | Rows | Size |
|------|------|------|
| `yellow_tripdata_2024-01.parquet` | 2,964,624 | 47.6 MB |
| `yellow_tripdata_2024-02.parquet` | 3,007,526 | 48.0 MB |
| `yellow_tripdata_2024-03.parquet` | 3,582,628 | 57.3 MB |
| **Total raw** | **9,554,778** | **152.9 MB** |

### After cleaning

| File | Rows kept | Dropped | Drop rate |
|------|-----------|---------|-----------|
| January 2024  | 2,713,591 | 251,033 | 8.5% |
| February 2024 | 2,709,891 | 297,635 | 9.9% |
| March 2024    | 3,024,564 | 558,064 | 15.6% |
| **Total clean** | **8,448,046** | **1,106,732** | **11.6%** |

Rows are dropped for: null timestamps or location IDs, pickup timestamps outside January-March 2024, zero/negative fares, implausible trip distances (>200 mi), trip durations outside 1–300 minutes, or passenger counts outside 1–6.

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- Python 3.10+

---

## Setup

### 1. Start the database

```bash
docker compose up -d
docker compose ps        # both services should show "Up"
```

| Service    | URL                  | Credentials                                   |
|------------|----------------------|-----------------------------------------------|
| PostgreSQL | `localhost:5433`     | user: `taxi` · password: `taxi` · db: `nyc_taxi_dw` |
| Adminer    | `http://localhost:8080` | System: PostgreSQL · Server: `postgres`    |

### 2. Create a Python virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

---

## Running the ETL Pipeline

Run these steps in order. Steps 1-4 are implemented.

```bash
# 1. Download raw Parquet files (~500 MB)
python etl/download.py

# 2. Clean and transform the data (~2–5 min)
python etl/clean.py

# 3. Apply the database schema
docker exec -i nyc_taxi_postgres psql -U taxi -d nyc_taxi_dw < sql/ddl.sql

# 4. Load all tables (~15–40 min for 8M+ rows)
python etl/load.py
```

### Verify the load

```bash
docker exec -it nyc_taxi_postgres psql -U taxi -d nyc_taxi_dw -c "SELECT COUNT(*) FROM fact_trip;"
# Expected: 8,448,046
```

---

## OLAP Queries

The 12 OLAP queries live in `sql/olap_queries.sql`, covering rollup, drill-down, slice, dice, ranking, and window operations.

Run them interactively:

```bash
docker exec -i nyc_taxi_postgres psql -U taxi -d nyc_taxi_dw < sql/olap_queries.sql
```

Export all query results to CSV for charts:

```bash
python etl/export_olap_results.py
ls output/result_q*.csv    # result_q1.csv ... result_q12.csv
```

---

## Visualizations

Use **Power BI** for the final visualizations. Recommended input: import the exported OLAP CSV files from `output/` instead of importing the full `fact_trip` table. The CSVs are smaller, already aggregated, and directly match the required charts.

```bash
python etl/export_olap_results.py
ls output/result_q*.csv
```

| Power BI visual | Source CSV | Suggested chart |
|-----------------|------------|-----------------|
| Revenue by month | `output/result_q2.csv` | Column/bar chart |
| Weekday vs weekend demand by hour | `output/result_q7.csv` | Line chart |
| Top 10 pickup zones | `output/result_q9.csv` | Horizontal bar chart |
| Tip percentage by payment type | `output/result_q10.csv` | Bar or pie chart |
| Trip duration by borough | `output/result_q4.csv` | Bar chart |
| Hour by day-of-week demand | `output/result_q7.csv` | Matrix heatmap |

Optional: connect Power BI directly to PostgreSQL at `localhost:5433`, database `nyc_taxi_dw`, user/password `taxi`/`taxi`. Use this only if you need interactive exploration beyond the exported OLAP results.

---

## Demo Flow

Use this sequence for a short project demonstration:

```bash
docker compose ps
docker exec -it nyc_taxi_postgres psql -U taxi -d nyc_taxi_dw -c "\dt"
docker exec -it nyc_taxi_postgres psql -U taxi -d nyc_taxi_dw -c "SELECT COUNT(*) FROM fact_trip;"
docker exec -i nyc_taxi_postgres psql -U taxi -d nyc_taxi_dw < sql/olap_queries.sql
```

Then show:

- Power BI dashboard built from `output/result_q*.csv`
- `docs/data_model.md` for the star schema explanation
- `docs/validation.md` for row-count checks
- `docs/report.md` as the living report draft

---

## Star Schema

```
                    DimTime
                   (time_id)
                       │
DimService ─────── FactTrip ─────── DimPickupLocation
(service_id)      (trip_id)         (location_id)
                       │
              DimDropoffLocation    DimPayment
              (location_id)         (payment_id)
```

**Grain:** one row = one taxi trip.

**Measures:** `fare_amount` · `tip_amount` · `total_amount` · `trip_distance` · `passenger_count` · `trip_duration`

---

## Project Structure

```
nyc-taxi-dw/
├── docker-compose.yml      ← PostgreSQL 16 + Adminer
├── requirements.txt
├── etl/
│   ├── download.py         ← fetch raw Parquet files
│   ├── clean.py            ← cleaning & transformation
│   ├── load.py             ← populate all DB tables
│   └── export_olap_results.py ← export query CSVs
├── sql/
│   ├── ddl.sql             ← CREATE TABLE statements
│   └── olap_queries.sql    ← 12 OLAP queries
├── docs/
│   ├── data_model.md       ← star schema and cleaning notes
│   ├── validation.md       ← row-count checks
│   ├── powerbi_notes.md    ← Power BI chart mapping
│   ├── report.md           ← report draft
│   ├── figures/            ← report figures
│   └── report/             ← final report source
├── output/result_q*.csv    ← OLAP exports for Power BI (git-ignored)
├── output/charts/          ← exported Power BI chart images (git-ignored)
├── diagrams/
│   ├── dfm.png             ← pending: Dimensional Fact Model
│   └── er.png              ← pending: Entity-Relationship diagram
├── data/raw/               ← Parquet files (git-ignored)
└── data/clean/             ← cleaned data (git-ignored)
```

---

## Stopping the Database

```bash
docker compose down          # stop, keep data
docker compose down -v       # stop and delete all data
```
