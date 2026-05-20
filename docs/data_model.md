# Data Model

This project implements a star-schema data warehouse for NYC TLC Yellow Taxi trips from January-March 2024.

## Grain

One row in `fact_trip` represents one cleaned taxi trip.

## Fact Table

`fact_trip`

Foreign keys:

- `time_id` -> `dim_time`
- `pickup_location_id` -> `dim_pickup_location`
- `dropoff_location_id` -> `dim_dropoff_location`
- `payment_id` -> `dim_payment`
- `service_id` -> `dim_service`

Measures:

- `fare_amount`
- `tip_amount`
- `total_amount`
- `trip_distance`
- `passenger_count`
- `trip_duration`

## Dimensions

`dim_time`

- Hierarchy: hour -> day -> month -> quarter -> year
- Grain: one row per pickup date and hour
- `day_of_week` uses ISO numbering: `1=Monday`, `7=Sunday`

`dim_pickup_location`

- Hierarchy: zone -> borough -> city
- Loaded from `data/raw/taxi_zone_lookup.csv`

`dim_dropoff_location`

- Hierarchy: zone -> borough -> city
- Loaded from `data/raw/taxi_zone_lookup.csv`

`dim_payment`

- Hierarchy: payment type -> payment category
- Static mapping of TLC payment codes

`dim_service`

- Hierarchy: vendor -> taxi service type
- Static mapping of TLC vendor IDs

## Cleaning Rules

Rows are removed when:

- pickup/dropoff timestamps or pickup/dropoff locations are missing
- pickup timestamp is outside `2024-01-01 <= pickup < 2024-04-01`
- `trip_distance <= 0` or `trip_distance >= 200`
- `fare_amount <= 0` or `fare_amount >= 500`
- `total_amount <= 0`
- `passenger_count` is outside 1-6
- computed `trip_duration` is outside 1-300 minutes

Missing `tip_amount` values are filled with `0`.

## Physical Schema

The report can present logical names as `DimTime`, `DimPickupLocation`, and `FactTrip`, but PostgreSQL uses lowercase physical table names:

- `dim_time`
- `dim_pickup_location`
- `dim_dropoff_location`
- `dim_payment`
- `dim_service`
- `fact_trip`
