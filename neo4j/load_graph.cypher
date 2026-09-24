// Rebuild the derived Neo4j graph from CSV files exported by PostgreSQL.
// Run after etl/export_neo4j_graph.py has written neo4j/import/*.csv.

CREATE CONSTRAINT pickup_zone_location_id IF NOT EXISTS
FOR (zone:PickupZone) REQUIRE zone.location_id IS UNIQUE;

CREATE CONSTRAINT dropoff_zone_location_id IF NOT EXISTS
FOR (zone:DropoffZone) REQUIRE zone.location_id IS UNIQUE;

CREATE CONSTRAINT payment_type_id IF NOT EXISTS
FOR (payment:PaymentType) REQUIRE payment.payment_id IS UNIQUE;

CREATE CONSTRAINT vendor_service_id IF NOT EXISTS
FOR (vendor:Vendor) REQUIRE vendor.service_id IS UNIQUE;

CREATE CONSTRAINT month_year_month IF NOT EXISTS
FOR (month:Month) REQUIRE month.year_month IS UNIQUE;

CREATE CONSTRAINT hour_value IF NOT EXISTS
FOR (hour:Hour) REQUIRE hour.hour IS UNIQUE;

// The graph is derived data, so clearing it makes a reload deterministic.
MATCH (node)
DETACH DELETE node;

LOAD CSV WITH HEADERS FROM 'file:///pickup_zones.csv' AS row
MERGE (zone:PickupZone {location_id: toInteger(row.location_id)})
SET zone.zone = row.zone,
    zone.borough = row.borough,
    zone.city = row.city;

LOAD CSV WITH HEADERS FROM 'file:///dropoff_zones.csv' AS row
MERGE (zone:DropoffZone {location_id: toInteger(row.location_id)})
SET zone.zone = row.zone,
    zone.borough = row.borough,
    zone.city = row.city;

LOAD CSV WITH HEADERS FROM 'file:///payment_types.csv' AS row
MERGE (payment:PaymentType {payment_id: toInteger(row.payment_id)})
SET payment.payment_type = row.payment_type,
    payment.payment_category = row.payment_category;

LOAD CSV WITH HEADERS FROM 'file:///vendors.csv' AS row
MERGE (vendor:Vendor {service_id: toInteger(row.service_id)})
SET vendor.vendor_id = toInteger(row.vendor_id),
    vendor.vendor_name = row.vendor_name,
    vendor.service_type = row.service_type;

LOAD CSV WITH HEADERS FROM 'file:///months.csv' AS row
MERGE (month:Month {year_month: row.year_month})
SET month.year = toInteger(row.year),
    month.month = toInteger(row.month);

LOAD CSV WITH HEADERS FROM 'file:///hours.csv' AS row
MERGE (hour:Hour {hour: toInteger(row.hour)});

LOAD CSV WITH HEADERS FROM 'file:///pickup_dropoff_flows.csv' AS row
MATCH (pickup:PickupZone {location_id: toInteger(row.pickup_location_id)})
MATCH (dropoff:DropoffZone {location_id: toInteger(row.dropoff_location_id)})
MERGE (pickup)-[flow:TRIPS_TO]->(dropoff)
SET flow.trip_count = toInteger(row.trip_count),
    flow.total_revenue = toFloat(row.total_revenue),
    flow.avg_distance_miles = toFloat(row.avg_distance_miles),
    flow.avg_duration_minutes = toFloat(row.avg_duration_minutes);

LOAD CSV WITH HEADERS FROM 'file:///pickup_payment_patterns.csv' AS row
MATCH (pickup:PickupZone {location_id: toInteger(row.pickup_location_id)})
MATCH (payment:PaymentType {payment_id: toInteger(row.payment_id)})
MERGE (pickup)-[pattern:PAID_WITH]->(payment)
SET pattern.trip_count = toInteger(row.trip_count),
    pattern.total_revenue = toFloat(row.total_revenue),
    pattern.avg_tip_percentage = toFloat(row.avg_tip_percentage);

LOAD CSV WITH HEADERS FROM 'file:///vendor_month_revenue.csv' AS row
MATCH (vendor:Vendor {service_id: toInteger(row.service_id)})
MATCH (month:Month {year_month: row.year_month})
MERGE (vendor)-[revenue:EARNED_IN]->(month)
SET revenue.trip_count = toInteger(row.trip_count),
    revenue.total_revenue = toFloat(row.total_revenue),
    revenue.avg_total_amount = toFloat(row.avg_total_amount);

LOAD CSV WITH HEADERS FROM 'file:///pickup_hour_demand.csv' AS row
MATCH (pickup:PickupZone {location_id: toInteger(row.pickup_location_id)})
MATCH (hour:Hour {hour: toInteger(row.hour)})
MERGE (pickup)-[demand:HAS_PICKUP_DEMAND]->(hour)
SET demand.trip_count = toInteger(row.trip_count),
    demand.total_revenue = toFloat(row.total_revenue);

MATCH (node)
RETURN labels(node) AS labels, count(*) AS node_count
ORDER BY labels;

MATCH ()-[relationship]->()
RETURN type(relationship) AS relationship_type, count(*) AS relationship_count
ORDER BY relationship_type;
