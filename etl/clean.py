import os
import pandas as pd

RAW_DIR   = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
CLEAN_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "clean")

PARQUET_FILES = [
    "yellow_tripdata_2024-01.parquet",
    "yellow_tripdata_2024-02.parquet",
    "yellow_tripdata_2024-03.parquet",
]


def clean(df: pd.DataFrame, filename: str) -> pd.DataFrame:
    before = len(df)

    # compute trip_duration in minutes before any filtering
    df["trip_duration"] = (
        (df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"])
        .dt.total_seconds() / 60
    )

    # drop rows with null keys
    df = df.dropna(subset=[
        "tpep_pickup_datetime", "tpep_dropoff_datetime",
        "PULocationID", "DOLocationID",
    ])

    # numeric range filters
    df = df[df["trip_distance"].between(0, 200, inclusive="neither")]
    df = df[df["fare_amount"].between(0, 500, inclusive="neither")]
    df = df[df["total_amount"] > 0]
    df = df[df["passenger_count"].between(1, 6)]
    df = df[df["trip_duration"].between(1, 300)]

    # fill nullable measure
    df["tip_amount"] = df["tip_amount"].fillna(0)

    after = len(df)
    dropped = before - after
    print(f"  {filename}: {before:>10,} → {after:>10,}  (dropped {dropped:,}, {dropped/before*100:.1f}%)")
    return df


if __name__ == "__main__":
    os.makedirs(CLEAN_DIR, exist_ok=True)

    total_before = 0
    total_after  = 0

    for filename in PARQUET_FILES:
        raw_path   = os.path.join(RAW_DIR, filename)
        clean_path = os.path.join(CLEAN_DIR, filename)

        df = pd.read_parquet(raw_path)
        total_before += len(df)

        df = clean(df, filename)
        total_after += len(df)

        df.to_parquet(clean_path, index=False)

    print(f"\n  TOTAL : {total_before:>10,} → {total_after:>10,}  "
          f"(dropped {total_before - total_after:,}, "
          f"{(total_before - total_after) / total_before * 100:.1f}%)")
    print(f"\n  Clean files written to: {os.path.abspath(CLEAN_DIR)}")
