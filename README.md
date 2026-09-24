# NYC Taxi Data Warehouse

**Course:** DM2526 - Data Management 2025/2026
**Dataset:** NYC TLC Yellow Taxi Trip Records, January-March 2024
**Stack:** PostgreSQL 16, Python 3.10+, pandas, SQLAlchemy, Neo4j 5

This project implements a PostgreSQL star-schema data warehouse for NYC Yellow
Taxi trips and a Neo4j graph layer for visual relationship exploration.
PostgreSQL is the source of truth; Neo4j is rebuilt from PostgreSQL aggregates.

## Results at a glance

| Stage | Result |
|---|---:|
| Raw TLC trips | 9,554,778 |
| Cleaned trips loaded in `fact_trip` | 8,448,046 |
| PostgreSQL dimensions | 5 |
| OLAP SQL queries | 12 |
| Neo4j nodes | 565 |
| Neo4j aggregate relationships | 39,590 |

The data-quality rules retain 88.4% of raw trips. See
[`docs/validation.md`](docs/validation.md) for counts and checks.

## Architecture

```text
NYC TLC Parquet files
        |
        v
Python ETL and cleaning
        |
        v
PostgreSQL star-schema warehouse
        |                       |
        v                       v
12 OLAP SQL queries     Neo4j aggregate CSV export
                                |
                                v
                    Neo4j Browser graph exploration
```

The graph stores aggregate taxi corridors and patterns, never one node per
trip. This keeps graph analysis responsive and traceable to the warehouse. See
[`docs/architecture.md`](docs/architecture.md) and
[`neo4j/graph_model.md`](neo4j/graph_model.md) for details.

## Prerequisites

- Docker and Docker Compose
- Python 3.10 or later

## Setup

Start PostgreSQL, Adminer, and Neo4j:

```bash
docker compose up -d
docker compose ps
```

| Service | Address | Credentials |
|---|---|---|
| PostgreSQL | `localhost:5433` | `taxi` / `taxi`, database `nyc_taxi_dw` |
| Adminer | [http://localhost:8080](http://localhost:8080) | PostgreSQL server `postgres` |
| Neo4j Browser | [http://localhost:7474](http://localhost:7474) | `neo4j` / `taxigraph2024` |
| Neo4j Bolt | `bolt://localhost:7687` | `neo4j` / `taxigraph2024` |

Create and activate the Python environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Build the warehouse

Run these steps in order when starting from raw data:

```bash
.venv/bin/python etl/download.py
.venv/bin/python etl/clean.py
docker exec -i nyc_taxi_postgres psql -U taxi -d nyc_taxi_dw < sql/ddl.sql
.venv/bin/python etl/load.py
```

Verify the expected fact-table count:

```bash
docker exec -it nyc_taxi_postgres psql -U taxi -d nyc_taxi_dw \
  -c "SELECT COUNT(*) FROM fact_trip;"
```

Expected output: `8,448,046` rows.

## Run OLAP analysis

The 12 SQL queries cover roll-up, drill-down, slice, dice, ranking, and window
operations.

```bash
docker exec -i nyc_taxi_postgres psql -U taxi -d nyc_taxi_dw < sql/olap_queries.sql
.venv/bin/python etl/export_olap_results.py
```

The generated `output/result_q1.csv` through `output/result_q12.csv` files are
ignored by Git because they can be reproduced from the warehouse.

## Run the Neo4j graph layer

Export graph aggregates, then load the graph:

```bash
.venv/bin/python etl/export_neo4j_graph.py
docker exec -i nyc_taxi_neo4j cypher-shell -u neo4j -p taxigraph2024 \
  -d neo4j < neo4j/load_graph.cypher
```

Open Neo4j Browser and run `neo4j/exploration_queries.cypher`. The queries
answer corridor, hub, payment-pattern, vendor, and hourly-demand questions. G1
is a presentation-friendly JFK Airport to Manhattan graph visualization.

```bash
docker exec -i nyc_taxi_neo4j cypher-shell -u neo4j -p taxigraph2024 \
  -d neo4j < neo4j/exploration_queries.cypher
```

Read [`docs/neo4j_notes.md`](docs/neo4j_notes.md) for the workflow and
[`docs/graph_analysis.md`](docs/graph_analysis.md) for validated results.

## Diagrams and report

The logical DFM and physical star-schema diagrams are ready for the submission:

- [`diagrams/dfm.png`](diagrams/dfm.png)
- [`diagrams/er.png`](diagrams/er.png)

The completed report is [`docs/report.md`](docs/report.md). Supporting
documentation covers the data model, diagram sources, validation, graph model,
and analysis findings.

## Demo flow

```bash
docker compose ps
docker exec -it nyc_taxi_postgres psql -U taxi -d nyc_taxi_dw \
  -c "SELECT COUNT(*) FROM fact_trip;"
docker exec -i nyc_taxi_postgres psql -U taxi -d nyc_taxi_dw < sql/olap_queries.sql
.venv/bin/python etl/export_neo4j_graph.py
docker exec -i nyc_taxi_neo4j cypher-shell -u neo4j -p taxigraph2024 \
  -d neo4j < neo4j/load_graph.cypher
```

Then show the diagrams, run G1 in Neo4j Browser, and use the report's findings
to explain how the graph complements the OLAP analysis.

## Project structure

```text
nyc-taxi-dw/
|- docker-compose.yml
|- etl/
|  |- clean.py
|  |- download.py
|  |- load.py
|  |- export_olap_results.py
|  `- export_neo4j_graph.py
|- sql/
|  |- ddl.sql
|  `- olap_queries.sql
|- neo4j/
|  |- load_graph.cypher
|  |- exploration_queries.cypher
|  |- graph_model.md
|  `- import/                 generated CSVs, ignored by Git
|- diagrams/
|  |- dfm.svg and dfm.png
|  `- er.svg and er.png
|- docs/
|  |- architecture.md
|  |- data_model.md
|  |- diagrams.md
|  |- graph_analysis.md
|  |- neo4j_notes.md
|  |- report.md
|  `- validation.md
|- data/raw/                  ignored raw data
|- data/clean/                ignored cleaned data
`- output/                    ignored OLAP CSV exports
```

## Stop services

```bash
docker compose down
```

This preserves PostgreSQL and Neo4j data volumes. `docker compose down -v`
removes both databases and should only be used when a complete rebuild is
intended.
