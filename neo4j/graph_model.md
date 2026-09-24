# Graph Model

Neo4j receives a compact, reproducible representation of warehouse aggregates.
It does not contain one node per trip. The PostgreSQL `fact_trip` table has more
than 8 million rows, while the graph has a bounded number of locations, payment
types, vendors, months, hours, and aggregated relationships.

## Nodes

| Label | Key | Source |
|---|---|---|
| `PickupZone` | `location_id` | `dim_pickup_location` |
| `DropoffZone` | `location_id` | `dim_dropoff_location` |
| `PaymentType` | `payment_id` | `dim_payment` |
| `Vendor` | `service_id` | `dim_service` |
| `Month` | `year_month` | `dim_time` |
| `Hour` | `hour` | generated values 0-23 |

Separate pickup and dropoff zone labels preserve the direction of a taxi flow,
even though both use the TLC location identifier.

## Relationships

| Relationship | From | To | Properties |
|---|---|---|---|
| `TRIPS_TO` | `PickupZone` | `DropoffZone` | trip count, revenue, average distance, average duration |
| `PAID_WITH` | `PickupZone` | `PaymentType` | trip count, revenue, average tip percentage |
| `EARNED_IN` | `Vendor` | `Month` | trip count, revenue, average total amount |
| `HAS_PICKUP_DEMAND` | `PickupZone` | `Hour` | trip count, revenue |

## Generated CSVs

Run the export from the repository root after PostgreSQL has been loaded:

```bash
.venv/bin/python etl/export_neo4j_graph.py
```

The generated files are written to `neo4j/import/`, which Docker mounts
read-only as Neo4j's `file:///` import directory. Re-running the command
replaces all graph-export files with fresh aggregates from PostgreSQL.
