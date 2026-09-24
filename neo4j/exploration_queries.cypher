// Graph exploration queries for Neo4j Browser and the project report.

// G1. Visualize the 100 busiest pickup-to-dropoff corridors.
MATCH (pickup:PickupZone)-[flow:TRIPS_TO]->(dropoff:DropoffZone)
WITH pickup, flow, dropoff
ORDER BY flow.trip_count DESC
LIMIT 100
RETURN pickup, flow, dropoff;

// G2. Top 10 corridors by trip count and total revenue.
MATCH (pickup:PickupZone)-[flow:TRIPS_TO]->(dropoff:DropoffZone)
RETURN
    pickup.borough AS pickup_borough,
    pickup.zone AS pickup_zone,
    dropoff.borough AS dropoff_borough,
    dropoff.zone AS dropoff_zone,
    flow.trip_count,
    flow.total_revenue,
    flow.avg_distance_miles,
    flow.avg_duration_minutes
ORDER BY flow.trip_count DESC
LIMIT 10;

// G3. Pickup hubs ranked by their total outgoing demand.
MATCH (pickup:PickupZone)-[flow:TRIPS_TO]->()
RETURN
    pickup.borough,
    pickup.zone,
    SUM(flow.trip_count) AS trip_count,
    ROUND(SUM(flow.total_revenue), 2) AS total_revenue,
    count(flow) AS distinct_destinations
ORDER BY trip_count DESC
LIMIT 10;

// G4. Payment preference for each busy pickup zone.
MATCH (pickup:PickupZone)-[pattern:PAID_WITH]->(payment:PaymentType)
WITH pickup, payment, pattern
ORDER BY pickup.zone, pattern.trip_count DESC
WITH pickup, collect({
    payment_type: payment.payment_type,
    trip_count: pattern.trip_count,
    total_revenue: pattern.total_revenue,
    avg_tip_percentage: pattern.avg_tip_percentage
})[0] AS preferred_payment
RETURN
    pickup.borough,
    pickup.zone,
    preferred_payment.payment_type AS preferred_payment_type,
    preferred_payment.trip_count,
    preferred_payment.total_revenue,
    preferred_payment.avg_tip_percentage
ORDER BY preferred_payment.trip_count DESC
LIMIT 20;

// G5. Vendor revenue by month.
MATCH (vendor:Vendor)-[revenue:EARNED_IN]->(month:Month)
RETURN
    month.year_month,
    vendor.vendor_name,
    revenue.trip_count,
    revenue.total_revenue,
    revenue.avg_total_amount
ORDER BY month.year_month, revenue.total_revenue DESC;

// G6. Busiest pickup hour for each zone with at least 10,000 trips.
MATCH (pickup:PickupZone)-[demand:HAS_PICKUP_DEMAND]->(hour:Hour)
WITH pickup, hour, demand
ORDER BY pickup.zone, demand.trip_count DESC
WITH pickup, collect({hour: hour.hour, trip_count: demand.trip_count})[0] AS peak
WHERE peak.trip_count >= 10000
RETURN pickup.borough, pickup.zone, peak.hour AS peak_hour, peak.trip_count
ORDER BY peak.trip_count DESC
LIMIT 20;
