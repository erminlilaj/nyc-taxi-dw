# Project Diagrams

The project contains two diagrams for the final submission:

- `diagrams/dfm.svg` and `diagrams/dfm.png`: the logical Dimensional Fact
  Model requested by the proposal. It presents the fact, measures, dimensions,
  and dimension hierarchies.
- `diagrams/er.svg` and `diagrams/er.png`: the physical PostgreSQL star schema.
  It uses the real table and key names from `sql/ddl.sql`.

The SVG files are the editable sources. The PNG files are presentation-ready
exports for the report or slides. Render them again from the repository root:

```bash
convert -background white diagrams/dfm.svg diagrams/dfm.png
convert -background white diagrams/er.svg diagrams/er.png
```

The DFM distinguishes the logical warehouse design from the Neo4j graph model,
which is documented separately in `neo4j/graph_model.md`.
