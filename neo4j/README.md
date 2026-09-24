# Neo4j Graph Layer

Neo4j is the optional graph-analysis and visualization component of the
project. PostgreSQL remains the source of truth; Neo4j only receives aggregates
exported from the warehouse.

## Start Neo4j

```bash
docker compose up -d neo4j
docker compose ps neo4j
```

Open [Neo4j Browser](http://localhost:7474) and sign in with:

- username: `neo4j`
- password: `taxigraph2024`

The Bolt endpoint is `bolt://localhost:7687`. The first Browser sign-in may ask
you to choose a new password; use that same password in the commands below if
you change it.

## Data lifecycle

1. `etl/export_neo4j_graph.py` reads PostgreSQL and writes generated CSV files
   to `neo4j/import/`.
2. `neo4j/load_graph.cypher` creates the graph schema and imports those files.
3. `neo4j/exploration_queries.cypher` contains the analysis queries used in the
   report and demo.

The CSV files are generated artifacts and are intentionally not versioned.

## Load or refresh the graph

```bash
.venv/bin/python etl/export_neo4j_graph.py
docker exec -i nyc_taxi_neo4j cypher-shell -u neo4j -p taxigraph2024 \
  -d neo4j < neo4j/load_graph.cypher
```

The loader clears and recreates the derived graph but does not touch PostgreSQL.
Use the scripts in `neo4j/exploration_queries.cypher` from Browser or
`cypher-shell` to explore the loaded graph.
