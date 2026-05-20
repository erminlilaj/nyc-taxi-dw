# NYC Taxi Data Warehouse

**Course:** DM2526 — Data Management 2025/2026
**Dataset:** NYC TLC Yellow Taxi Trip Records — January, February, March 2024
**Stack:** PostgreSQL 16 · Python 3.10+ · pandas · SQLAlchemy · matplotlib/seaborn

A star-schema data warehouse built on ~8.4 million taxi trip records, with a full ETL pipeline, 12 OLAP queries, and 6 visualizations.

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
| January 2024  | 2,713,605 | 251,019 | 8.5% |
| February 2024 | 2,709,893 | 297,633 | 9.9% |
| March 2024    | 3,024,567 | 558,061 | 15.6% |
| **Total clean** | **8,448,065** | **1,106,713** | **11.6%** |

Rows are dropped for: null timestamps or location IDs, zero/negative fares, implausible trip distances (>200 mi), trip durations outside 1–300 minutes, or passenger counts outside 1–6.

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

Run these steps in order:

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
docker exec -it nyc_taxi_postgres psql -U taxi -d nyc_taxi_dw -c "SELECT COUNT(*) FROM FactTrip;"
# Expected: 8,000,000+
```

---

## OLAP Queries

All 12 queries are in `sql/olap_queries.sql`, covering rollup, drill-down, slice, dice, ranking, and window operations.

Run them interactively:

```bash
docker exec -it nyc_taxi_postgres psql -U taxi -d nyc_taxi_dw -f sql/olap_queries.sql
```

Export a query result to CSV (inside psql):

```sql
\copy (SELECT ...) TO 'output/result_q1.csv' CSV HEADER;
```

---

## Visualizations

After exporting all query CSVs:

```bash
python viz/charts.py
ls output/charts/    # 6 PNG files
```

| Chart file                   | Description                        |
|------------------------------|------------------------------------|
| `01_revenue_by_month.png`    | Total revenue — Jan / Feb / Mar    |
| `02_demand_by_hour.png`      | Weekday vs weekend demand by hour  |
| `03_top10_zones.png`         | Top 10 pickup zones by trip count  |
| `04_tip_by_payment.png`      | Avg tip % by payment type          |
| `05_duration_by_borough.png` | Avg trip duration by borough       |
| `06_heatmap_hour_dow.png`    | Heatmap — hour × day of week       |

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
│   └── load.py             ← populate all DB tables
├── sql/
│   ├── ddl.sql             ← CREATE TABLE statements
│   └── olap_queries.sql    ← 12 OLAP queries
├── viz/
│   └── charts.py           ← generate 6 PNG charts
├── diagrams/
│   ├── dfm.png             ← Dimensional Fact Model
│   └── er.png              ← Entity-Relationship diagram
├── output/charts/          ← generated PNGs (git-ignored)
├── data/raw/               ← Parquet files (git-ignored)
└── data/clean/             ← cleaned data (git-ignored)
```

---

## Stopping the Database

```bash
docker compose down          # stop, keep data
docker compose down -v       # stop and delete all data
```
