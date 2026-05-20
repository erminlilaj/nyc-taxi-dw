import io
import os
from typing import Iterable

import pandas as pd
import psycopg2
import pyarrow.parquet as pq


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
CLEAN_DIR = os.path.join(BASE_DIR, "data", "clean")

ZONE_LOOKUP_FILE = os.path.join(RAW_DIR, "taxi_zone_lookup.csv")
PARQUET_FILES = [
    "yellow_tripdata_2024-01.parquet",
    "yellow_tripdata_2024-02.parquet",
    "yellow_tripdata_2024-03.parquet",
]

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5433")),
    "dbname": os.getenv("DB_NAME", "nyc_taxi_dw"),
    "user": os.getenv("DB_USER", "taxi"),
    "password": os.getenv("DB_PASSWORD", "taxi"),
}

FACT_BATCH_SIZE = 100_000
FACT_COLUMNS = [
    "time_id",
    "pickup_location_id",
    "dropoff_location_id",
    "payment_id",
    "service_id",
    "fare_amount",
    "tip_amount",
    "total_amount",
    "trip_distance",
    "passenger_count",
    "trip_duration",
]
SOURCE_FACT_COLUMNS = [
    "VendorID",
    "tpep_pickup_datetime",
    "PULocationID",
    "DOLocationID",
    "payment_type",
    "fare_amount",
    "tip_amount",
    "total_amount",
    "trip_distance",
    "passenger_count",
    "trip_duration",
]


def connect():
    return psycopg2.connect(**DB_CONFIG)


def copy_dataframe(conn, table: str, df: pd.DataFrame, columns: Iterable[str]) -> int:
    columns = list(columns)
    if df.empty:
        return 0

    buffer = io.StringIO()
    df.to_csv(buffer, index=False, header=False, columns=columns, na_rep="\\N")
    buffer.seek(0)

    column_sql = ", ".join(columns)
    sql = (
        f"COPY {table} ({column_sql}) "
        "FROM STDIN WITH (FORMAT CSV, NULL '\\N')"
    )
    with conn.cursor() as cur:
        cur.copy_expert(sql, buffer)
    return len(df)


def reset_tables(conn):
    print("Resetting warehouse tables ...")
    with conn.cursor() as cur:
        cur.execute(
            """
            TRUNCATE TABLE
                fact_trip,
                dim_time,
                dim_pickup_location,
                dim_dropoff_location,
                dim_payment,
                dim_service
            RESTART IDENTITY CASCADE;
            """
        )
    conn.commit()


def load_payment(conn):
    df = pd.DataFrame(
        [
            (1, "Credit card", "Electronic"),
            (2, "Cash", "Cash"),
            (3, "No charge", "Other"),
            (4, "Dispute", "Other"),
            (5, "Unknown", "Other"),
            (6, "Voided trip", "Other"),
        ],
        columns=["payment_id", "payment_type", "payment_category"],
    )
    rows = copy_dataframe(conn, "dim_payment", df, df.columns)
    conn.commit()
    print(f"Loaded dim_payment: {rows:,} rows")


def load_service(conn):
    df = pd.DataFrame(
        [
            (1, 1, "Creative Mobile Technologies", "Yellow Taxi"),
            (2, 2, "VeriFone Inc.", "Yellow Taxi"),
        ],
        columns=["service_id", "vendor_id", "vendor_name", "service_type"],
    )
    rows = copy_dataframe(conn, "dim_service", df, df.columns)
    conn.commit()
    print(f"Loaded dim_service: {rows:,} rows")


def load_locations(conn):
    zones = pd.read_csv(ZONE_LOOKUP_FILE)
    locations = zones.rename(
        columns={
            "LocationID": "location_id",
            "Zone": "zone",
            "Borough": "borough",
        }
    )[["location_id", "zone", "borough"]].copy()
    locations["zone"] = locations["zone"].fillna("Unknown")
    locations["borough"] = locations["borough"].fillna("Unknown")
    locations["city"] = "New York City"

    rows_pickup = copy_dataframe(conn, "dim_pickup_location", locations, locations.columns)
    rows_dropoff = copy_dataframe(conn, "dim_dropoff_location", locations, locations.columns)
    conn.commit()
    print(f"Loaded dim_pickup_location: {rows_pickup:,} rows")
    print(f"Loaded dim_dropoff_location: {rows_dropoff:,} rows")


def load_time(conn):
    parts = []
    for filename in PARQUET_FILES:
        path = os.path.join(CLEAN_DIR, filename)
        df = pd.read_parquet(path, columns=["tpep_pickup_datetime"])
        pickup = df["tpep_pickup_datetime"]
        part = pd.DataFrame(
            {
                "pickup_date": pickup.dt.date,
                "hour": pickup.dt.hour.astype("int16"),
            }
        ).drop_duplicates()
        parts.append(part)

    time_df = pd.concat(parts, ignore_index=True).drop_duplicates()
    pickup_date = pd.to_datetime(time_df["pickup_date"])
    time_df["year"] = pickup_date.dt.year.astype("int16")
    time_df["quarter"] = pickup_date.dt.quarter.astype("int16")
    time_df["month"] = pickup_date.dt.month.astype("int16")
    time_df["day"] = pickup_date.dt.day.astype("int16")
    time_df["day_of_week"] = pickup_date.dt.isocalendar().day.astype("int16")
    time_df["is_weekend"] = time_df["day_of_week"].isin([6, 7])
    time_df = time_df[
        [
            "pickup_date",
            "year",
            "quarter",
            "month",
            "day",
            "hour",
            "day_of_week",
            "is_weekend",
        ]
    ].sort_values(["pickup_date", "hour"])

    rows = copy_dataframe(conn, "dim_time", time_df, time_df.columns)
    conn.commit()
    print(f"Loaded dim_time: {rows:,} rows")
    return get_time_lookup(conn)


def get_time_lookup(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT time_id, pickup_date, hour FROM dim_time;")
        rows = cur.fetchall()
    return {(pickup_date.isoformat(), hour): time_id for time_id, pickup_date, hour in rows}


def fact_batches(filename: str, time_lookup: dict):
    path = os.path.join(CLEAN_DIR, filename)
    parquet_file = pq.ParquetFile(path)
    for batch in parquet_file.iter_batches(
        batch_size=FACT_BATCH_SIZE,
        columns=SOURCE_FACT_COLUMNS,
    ):
        source = batch.to_pandas()
        pickup = source["tpep_pickup_datetime"]
        pickup_date = pickup.dt.strftime("%Y-%m-%d")
        pickup_hour = pickup.dt.hour

        time_ids = [
            time_lookup[(date, hour)]
            for date, hour in zip(pickup_date, pickup_hour)
        ]

        fact = pd.DataFrame(
            {
                "time_id": time_ids,
                "pickup_location_id": source["PULocationID"].astype("int32"),
                "dropoff_location_id": source["DOLocationID"].astype("int32"),
                "payment_id": source["payment_type"].astype("int16"),
                "service_id": source["VendorID"].astype("int16"),
                "fare_amount": source["fare_amount"],
                "tip_amount": source["tip_amount"].fillna(0),
                "total_amount": source["total_amount"],
                "trip_distance": source["trip_distance"],
                "passenger_count": source["passenger_count"].astype("int16"),
                "trip_duration": source["trip_duration"],
            }
        )
        yield fact


def load_fact(conn, time_lookup):
    total_rows = 0
    for filename in PARQUET_FILES:
        file_rows = 0
        print(f"Loading fact rows from {filename} ...")
        for fact in fact_batches(filename, time_lookup):
            rows = copy_dataframe(conn, "fact_trip", fact, FACT_COLUMNS)
            conn.commit()
            file_rows += rows
            total_rows += rows
            if file_rows % 500_000 < FACT_BATCH_SIZE:
                print(f"  {filename}: {file_rows:,} rows loaded")
        print(f"Loaded {filename}: {file_rows:,} fact rows")
    print(f"Loaded fact_trip: {total_rows:,} rows")


def print_table_counts(conn):
    tables = [
        "dim_payment",
        "dim_service",
        "dim_pickup_location",
        "dim_dropoff_location",
        "dim_time",
        "fact_trip",
    ]
    with conn.cursor() as cur:
        print("\nTable counts:")
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table};")
            count = cur.fetchone()[0]
            print(f"  {table:24s} {count:>10,}")


def main():
    expected_files = [ZONE_LOOKUP_FILE] + [
        os.path.join(CLEAN_DIR, filename) for filename in PARQUET_FILES
    ]
    missing = [path for path in expected_files if not os.path.exists(path)]
    if missing:
        raise FileNotFoundError("Missing required input files: " + ", ".join(missing))

    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SET synchronous_commit TO off;")
        reset_tables(conn)
        load_payment(conn)
        load_service(conn)
        load_locations(conn)
        time_lookup = load_time(conn)
        load_fact(conn, time_lookup)
        print_table_counts(conn)


if __name__ == "__main__":
    main()
