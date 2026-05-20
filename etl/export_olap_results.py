import csv
import os
import re

import psycopg2


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
QUERY_FILE = os.path.join(BASE_DIR, "sql", "olap_queries.sql")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5433")),
    "dbname": os.getenv("DB_NAME", "nyc_taxi_dw"),
    "user": os.getenv("DB_USER", "taxi"),
    "password": os.getenv("DB_PASSWORD", "taxi"),
}

QUERY_HEADER = re.compile(r"^-- Q(\d+)\b.*$", re.MULTILINE)


def load_queries():
    with open(QUERY_FILE, "r", encoding="utf-8") as f:
        sql = f.read()

    matches = list(QUERY_HEADER.finditer(sql))
    queries = []
    for index, match in enumerate(matches):
        query_number = int(match.group(1))
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(sql)
        query = sql[start:end].strip().rstrip(";")
        query = "\n".join(
            line for line in query.splitlines()
            if not line.lstrip().startswith("\\")
        ).strip()
        queries.append((query_number, query))

    if [number for number, _ in queries] != list(range(1, 13)):
        raise ValueError("Expected exactly queries Q1 through Q12 in olap_queries.sql")
    return queries


def export_query(cursor, query_number: int, query: str):
    cursor.execute(query)
    columns = [desc.name for desc in cursor.description]
    rows = cursor.fetchall()

    path = os.path.join(OUTPUT_DIR, f"result_q{query_number}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)

    print(f"Exported result_q{query_number}.csv: {len(rows):,} rows")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    queries = load_queries()

    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            for query_number, query in queries:
                export_query(cur, query_number, query)


if __name__ == "__main__":
    main()
