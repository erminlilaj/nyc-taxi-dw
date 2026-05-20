# Project Report Draft

## 1. Introduction

This project designs and implements a data warehouse for NYC TLC Yellow Taxi trip records from January-March 2024. The objective is to support OLAP analysis of trip demand, revenue, payment behavior, trip duration, and geographic patterns.

## 2. Dataset

Source: NYC TLC Yellow Taxi Trip Records.

Files used:

- `yellow_tripdata_2024-01.parquet`
- `yellow_tripdata_2024-02.parquet`
- `yellow_tripdata_2024-03.parquet`
- `taxi_zone_lookup.csv`

Raw data contains 9,554,778 trip rows. After cleaning, 8,448,046 rows remain.

## 3. ETL Pipeline

The ETL pipeline has three main scripts:

- `etl/download.py`: downloads raw Parquet files and the zone lookup CSV
- `etl/clean.py`: applies cleaning rules and writes cleaned Parquet files
- `etl/load.py`: loads dimensions and fact rows into PostgreSQL

Cleaning removes invalid timestamps, out-of-scope dates, invalid distances/fares, invalid passenger counts, and trips with implausible duration.

## 4. Data Warehouse Design

The warehouse uses a star schema.

Fact table:

- `fact_trip`

Dimensions:

- `dim_time`
- `dim_pickup_location`
- `dim_dropoff_location`
- `dim_payment`
- `dim_service`

The grain is one row per cleaned taxi trip.

See `docs/data_model.md` for the detailed schema explanation.

## 5. OLAP Queries

The 12 OLAP queries are stored in `sql/olap_queries.sql`.

They cover:

- rollup
- drill-down
- slice
- dice
- ranking
- window functions

The query result CSVs are exported with `etl/export_olap_results.py`.

## 6. Visualizations

Power BI is used for the visualization layer. The dashboard uses exported OLAP CSV files from `output/` as inputs.

Required charts:

- revenue by month
- weekday vs weekend demand by hour
- top 10 pickup zones
- tip percentage by payment type
- average trip duration by borough
- hour by day-of-week demand heatmap

See `docs/powerbi_notes.md` for the chart mapping.

## 7. Conclusions

To be completed after Power BI charts, diagrams, and final analysis are finished.
