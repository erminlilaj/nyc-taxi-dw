# Architecture

This project uses a two-layer analytical architecture for NYC TLC Yellow Taxi
trips from January through March 2024.

```text
NYC TLC Parquet files
        |
        v
Python cleaning and loading ETL
        |
        v
PostgreSQL star-schema warehouse
        |
        +-- SQL OLAP queries and CSV exports
        |
        +-- aggregated graph export
                 |
                 v
              Neo4j graph analysis and visualization
```

## PostgreSQL: system of record

PostgreSQL is the authoritative data warehouse. It stores the cleaned trip data
at the grain of one fact row per taxi trip, together with the time, pickup
location, dropoff location, payment, and service dimensions. Cleaning rules,
data-quality checks, dimensional hierarchies, and the 12 OLAP queries belong to
this layer.

Neo4j does not replace the warehouse, the ETL pipeline, or the OLAP SQL. It is
a derived analytical layer built from aggregated PostgreSQL results. This keeps
the graph small enough to explore while preserving an auditable path back to the
warehouse.

## Neo4j: relationship exploration layer

Neo4j represents meaningful aggregates as graph relationships rather than
individual trips. It supports visual and query-based exploration of:

- pickup-zone to dropoff-zone taxi corridors;
- pickup-zone payment preferences;
- vendor performance by month; and
- pickup-zone demand by hour.

Every relationship includes aggregate measures such as trip count, total
revenue, average distance, or average duration. The data is recreated by the
export and load commands, so it is never manually maintained.

## Why this meets the project objective

The course project requires a data warehouse with OLAP analysis. PostgreSQL
fulfills that core requirement through the implemented star schema and SQL
queries. The proposal lists Power BI/Tableau as optional technology; Neo4j is
used instead as the optional visualization and relationship-analysis component.
