# Neo4j Notes

Neo4j replaces the optional Power BI/Tableau component in the proposal. It is a
graph-analysis and visualization layer, not the primary data warehouse.

## What Neo4j adds

| Question | Graph representation | Query file |
|---|---|---|
| Which taxi corridors are busiest? | `PickupZone-[:TRIPS_TO]->DropoffZone` | G1-G3 |
| Which payment type dominates an area? | `PickupZone-[:PAID_WITH]->PaymentType` | G4 |
| How do vendors perform across months? | `Vendor-[:EARNED_IN]->Month` | G5 |
| When do pickup zones peak? | `PickupZone-[:HAS_PICKUP_DEMAND]->Hour` | G6 |

Relationship properties retain the relevant measures: trip count, total
revenue, average distance, average duration, and average tip percentage.

## Run the visualization layer

```bash
docker compose up -d neo4j
.venv/bin/python etl/export_neo4j_graph.py
docker exec -i nyc_taxi_neo4j cypher-shell -u neo4j -p taxigraph2024 \
  -d neo4j < neo4j/load_graph.cypher
```

Open [Neo4j Browser](http://localhost:7474), sign in with `neo4j` /
`taxigraph2024`, and run any query from `neo4j/exploration_queries.cypher`.
The first query is deliberately constrained to 20 JFK-to-Manhattan corridors,
which keeps the Browser graph readable for a presentation screenshot.

## Scope boundary

PostgreSQL is still responsible for cleaning, star-schema storage, and all
standard OLAP operations. Neo4j receives only regenerated aggregates from the
warehouse. See `docs/architecture.md` and `neo4j/graph_model.md` for the full
design rationale.
