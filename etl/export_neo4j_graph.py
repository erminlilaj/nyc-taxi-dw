"""Export aggregated PostgreSQL warehouse data for the Neo4j graph layer."""

import argparse
import os
from pathlib import Path

import psycopg2


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = BASE_DIR / "neo4j" / "import"

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5433")),
    "dbname": os.getenv("DB_NAME", "nyc_taxi_dw"),
    "user": os.getenv("DB_USER", "taxi"),
    "password": os.getenv("DB_PASSWORD", "taxi"),
}

EXPORTS = {
    "pickup_zones.csv": """
        SELECT location_id, zone, borough, city
        FROM dim_pickup_location
        ORDER BY location_id
    """,
    "dropoff_zones.csv": """
        SELECT location_id, zone, borough, city
        FROM dim_dropoff_location
        ORDER BY location_id
    """,
    "payment_types.csv": """
        SELECT payment_id, payment_type, payment_category
        FROM dim_payment
        ORDER BY payment_id
    """,
    "vendors.csv": """
        SELECT service_id, vendor_id, vendor_name, service_type
        FROM dim_service
        ORDER BY service_id
    """,
    "months.csv": """
        SELECT DISTINCT
            to_char(pickup_date, 'YYYY-MM') AS year_month,
            year,
            month
        FROM dim_time
        ORDER BY year_month
    """,
    "hours.csv": """
        SELECT hour
        FROM generate_series(0, 23) AS hour
        ORDER BY hour
    """,
    "pickup_dropoff_flows.csv": """
        SELECT
            f.pickup_location_id,
            f.dropoff_location_id,
            COUNT(*) AS trip_count,
            ROUND(SUM(f.total_amount), 2) AS total_revenue,
            ROUND(AVG(f.trip_distance), 2) AS avg_distance_miles,
            ROUND(AVG(f.trip_duration), 2) AS avg_duration_minutes
        FROM fact_trip AS f
        GROUP BY f.pickup_location_id, f.dropoff_location_id
        ORDER BY trip_count DESC, f.pickup_location_id, f.dropoff_location_id
    """,
    "pickup_payment_patterns.csv": """
        SELECT
            f.pickup_location_id,
            f.payment_id,
            COUNT(*) AS trip_count,
            ROUND(SUM(f.total_amount), 2) AS total_revenue,
            ROUND(
                AVG(f.tip_amount / NULLIF(f.fare_amount, 0)) * 100,
                2
            ) AS avg_tip_percentage
        FROM fact_trip AS f
        GROUP BY f.pickup_location_id, f.payment_id
        ORDER BY f.pickup_location_id, f.payment_id
    """,
    "vendor_month_revenue.csv": """
        SELECT
            f.service_id,
            to_char(t.pickup_date, 'YYYY-MM') AS year_month,
            COUNT(*) AS trip_count,
            ROUND(SUM(f.total_amount), 2) AS total_revenue,
            ROUND(AVG(f.total_amount), 2) AS avg_total_amount
        FROM fact_trip AS f
        JOIN dim_time AS t ON f.time_id = t.time_id
        GROUP BY f.service_id, to_char(t.pickup_date, 'YYYY-MM')
        ORDER BY f.service_id, year_month
    """,
    "pickup_hour_demand.csv": """
        SELECT
            f.pickup_location_id,
            t.hour,
            COUNT(*) AS trip_count,
            ROUND(SUM(f.total_amount), 2) AS total_revenue
        FROM fact_trip AS f
        JOIN dim_time AS t ON f.time_id = t.time_id
        GROUP BY f.pickup_location_id, t.hour
        ORDER BY f.pickup_location_id, t.hour
    """,
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Export aggregated PostgreSQL data for Neo4j CSV import."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for generated CSV files (default: {DEFAULT_OUTPUT_DIR})",
    )
    return parser.parse_args()


def export_csv(cursor, output_path: Path, query: str) -> None:
    copy_sql = f"COPY ({query}) TO STDOUT WITH (FORMAT CSV, HEADER TRUE)"
    with output_path.open("w", encoding="utf-8", newline="") as output_file:
        cursor.copy_expert(copy_sql, output_file)


def main():
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cursor:
            for filename, query in EXPORTS.items():
                output_path = output_dir / filename
                export_csv(cursor, output_path, query)
                print(f"Exported {filename}: {output_path.stat().st_size:,} bytes")

    print(f"\nNeo4j CSV export complete: {output_dir}")


if __name__ == "__main__":
    main()
