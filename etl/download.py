import os
import requests
from tqdm import tqdm

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

FILES = {
    "yellow_tripdata_2024-01.parquet": "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet",
    "yellow_tripdata_2024-02.parquet": "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-02.parquet",
    "yellow_tripdata_2024-03.parquet": "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-03.parquet",
    "taxi_zone_lookup.csv":            "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv",
}


def download(filename, url, dest_dir):
    path = os.path.join(dest_dir, filename)
    if os.path.exists(path):
        print(f"  already exists, skipping: {filename}")
        return

    print(f"  downloading {filename} ...")
    response = requests.get(url, stream=True, timeout=120)
    response.raise_for_status()

    total = int(response.headers.get("content-length", 0))
    with open(path, "wb") as f, tqdm(
        total=total, unit="B", unit_scale=True, unit_divisor=1024, leave=False
    ) as bar:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)
            bar.update(len(chunk))

    size_mb = os.path.getsize(path) / 1_048_576
    print(f"  saved {filename} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    os.makedirs(RAW_DIR, exist_ok=True)
    print(f"Destination: {os.path.abspath(RAW_DIR)}\n")

    for filename, url in FILES.items():
        download(filename, url, RAW_DIR)

    print("\nAll files present:")
    for filename in FILES:
        path = os.path.join(RAW_DIR, filename)
        size_mb = os.path.getsize(path) / 1_048_576
        print(f"  {filename:45s}  {size_mb:7.1f} MB")
