-- NYC Taxi Data Warehouse OLAP queries.
-- Run with:
--   docker exec -i nyc_taxi_postgres psql -U taxi -d nyc_taxi_dw < sql/olap_queries.sql

\pset pager off

-- Q1 - Rollup: trip count by hour -> day -> month.
SELECT
    t.month,
    t.pickup_date,
    t.hour,
    CASE
        WHEN GROUPING(t.month) = 1 THEN 'grand_total'
        WHEN GROUPING(t.pickup_date) = 1 THEN 'month_total'
        WHEN GROUPING(t.hour) = 1 THEN 'day_total'
        ELSE 'hour'
    END AS rollup_level,
    COUNT(*) AS trip_count
FROM fact_trip AS f
JOIN dim_time AS t ON f.time_id = t.time_id
GROUP BY ROLLUP (t.month, t.pickup_date, t.hour)
ORDER BY t.month NULLS LAST, t.pickup_date NULLS LAST, t.hour NULLS LAST;

-- Q2 - Rollup: total revenue by quarter with monthly detail.
SELECT
    t.quarter,
    t.month,
    CASE
        WHEN GROUPING(t.quarter) = 1 THEN 'grand_total'
        WHEN GROUPING(t.month) = 1 THEN 'quarter_total'
        ELSE 'month'
    END AS rollup_level,
    COUNT(*) AS trip_count,
    ROUND(SUM(f.total_amount), 2) AS total_revenue,
    ROUND(AVG(f.total_amount), 2) AS avg_total_amount
FROM fact_trip AS f
JOIN dim_time AS t ON f.time_id = t.time_id
GROUP BY ROLLUP (t.quarter, t.month)
ORDER BY t.quarter NULLS LAST, t.month NULLS LAST;

-- Q3 - Drill-down: average fare from city -> borough -> pickup zone.
SELECT
    l.city,
    l.borough,
    l.zone,
    COUNT(*) AS trip_count,
    ROUND(AVG(f.fare_amount), 2) AS avg_fare_amount,
    ROUND(AVG(f.total_amount), 2) AS avg_total_amount
FROM fact_trip AS f
JOIN dim_pickup_location AS l ON f.pickup_location_id = l.location_id
GROUP BY l.city, l.borough, l.zone
ORDER BY l.city, l.borough, trip_count DESC, l.zone;

-- Q4 - Drill-down: average trip duration by pickup borough.
SELECT
    l.city,
    l.borough,
    COUNT(*) AS trip_count,
    ROUND(AVG(f.trip_duration), 2) AS avg_trip_duration_minutes,
    ROUND(AVG(f.trip_distance), 2) AS avg_trip_distance
FROM fact_trip AS f
JOIN dim_pickup_location AS l ON f.pickup_location_id = l.location_id
GROUP BY l.city, l.borough
ORDER BY avg_trip_duration_minutes DESC;

-- Q5 - Slice: January trips only, summarized by pickup date.
SELECT
    t.pickup_date,
    COUNT(*) AS trip_count,
    ROUND(SUM(f.total_amount), 2) AS total_revenue,
    ROUND(AVG(f.passenger_count), 2) AS avg_passenger_count,
    ROUND(AVG(f.trip_distance), 2) AS avg_trip_distance
FROM fact_trip AS f
JOIN dim_time AS t ON f.time_id = t.time_id
WHERE t.month = 1
GROUP BY t.pickup_date
ORDER BY t.pickup_date;

-- Q6 - Slice: cash-payment trips only, summarized by month.
SELECT
    t.month,
    p.payment_type,
    COUNT(*) AS trip_count,
    ROUND(SUM(f.total_amount), 2) AS total_revenue,
    ROUND(AVG(f.total_amount), 2) AS avg_total_amount
FROM fact_trip AS f
JOIN dim_time AS t ON f.time_id = t.time_id
JOIN dim_payment AS p ON f.payment_id = p.payment_id
WHERE p.payment_type = 'Cash'
GROUP BY t.month, p.payment_type
ORDER BY t.month;

-- Q7 - Dice: weekday/weekend demand by hour and day of week.
SELECT
    t.hour,
    t.day_of_week,
    CASE WHEN t.is_weekend THEN 'Weekend' ELSE 'Weekday' END AS day_type,
    COUNT(*) AS trip_count,
    ROUND(SUM(f.total_amount), 2) AS total_revenue
FROM fact_trip AS f
JOIN dim_time AS t ON f.time_id = t.time_id
GROUP BY t.hour, t.day_of_week, t.is_weekend
ORDER BY t.hour, t.day_of_week;

-- Q8 - Dice: trip length category by payment type.
WITH trip_length_payment AS (
    SELECT
        CASE
            WHEN f.trip_distance < 1 THEN '0-1 mi'
            WHEN f.trip_distance < 3 THEN '1-3 mi'
            WHEN f.trip_distance < 5 THEN '3-5 mi'
            WHEN f.trip_distance < 10 THEN '5-10 mi'
            ELSE '10+ mi'
        END AS trip_length_category,
        CASE
            WHEN f.trip_distance < 1 THEN 1
            WHEN f.trip_distance < 3 THEN 2
            WHEN f.trip_distance < 5 THEN 3
            WHEN f.trip_distance < 10 THEN 4
            ELSE 5
        END AS category_sort,
        p.payment_type,
        f.total_amount,
        f.tip_amount
    FROM fact_trip AS f
    JOIN dim_payment AS p ON f.payment_id = p.payment_id
)
SELECT
    trip_length_category,
    payment_type,
    COUNT(*) AS trip_count,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(AVG(tip_amount), 2) AS avg_tip_amount
FROM trip_length_payment
GROUP BY trip_length_category, category_sort, payment_type
ORDER BY category_sort, payment_type;

-- Q9 - Ranking: top 10 pickup zones by trip count.
SELECT
    l.borough,
    l.zone,
    COUNT(*) AS trip_count,
    ROUND(SUM(f.total_amount), 2) AS total_revenue,
    RANK() OVER (ORDER BY COUNT(*) DESC) AS trip_count_rank
FROM fact_trip AS f
JOIN dim_pickup_location AS l ON f.pickup_location_id = l.location_id
GROUP BY l.borough, l.zone
ORDER BY trip_count_rank, l.borough, l.zone
LIMIT 10;

-- Q10 - Ranking: average tip percentage by payment type.
SELECT
    p.payment_type,
    p.payment_category,
    COUNT(*) AS trip_count,
    ROUND(SUM(f.tip_amount), 2) AS total_tips,
    ROUND(SUM(f.fare_amount), 2) AS total_fares,
    ROUND(AVG(f.tip_amount / NULLIF(f.fare_amount, 0)) * 100, 2) AS avg_tip_percentage,
    RANK() OVER (
        ORDER BY AVG(f.tip_amount / NULLIF(f.fare_amount, 0)) DESC
    ) AS tip_percentage_rank
FROM fact_trip AS f
JOIN dim_payment AS p ON f.payment_id = p.payment_id
GROUP BY p.payment_type, p.payment_category
ORDER BY tip_percentage_rank, p.payment_type;

-- Q11 - Window: peak hour rank per pickup borough.
WITH hourly_borough_demand AS (
    SELECT
        l.borough,
        t.hour,
        COUNT(*) AS trip_count
    FROM fact_trip AS f
    JOIN dim_time AS t ON f.time_id = t.time_id
    JOIN dim_pickup_location AS l ON f.pickup_location_id = l.location_id
    GROUP BY l.borough, t.hour
)
SELECT
    borough,
    hour,
    trip_count,
    RANK() OVER (PARTITION BY borough ORDER BY trip_count DESC) AS borough_hour_rank
FROM hourly_borough_demand
ORDER BY borough, borough_hour_rank, hour;

-- Q12 - Window: monthly revenue per vendor with month-over-month change.
WITH monthly_vendor_revenue AS (
    SELECT
        s.vendor_name,
        t.month,
        COUNT(*) AS trip_count,
        ROUND(SUM(f.total_amount), 2) AS total_revenue
    FROM fact_trip AS f
    JOIN dim_time AS t ON f.time_id = t.time_id
    JOIN dim_service AS s ON f.service_id = s.service_id
    GROUP BY s.vendor_name, t.month
)
SELECT
    vendor_name,
    month,
    trip_count,
    total_revenue,
    total_revenue
        - LAG(total_revenue) OVER (PARTITION BY vendor_name ORDER BY month)
        AS revenue_change_from_previous_month,
    RANK() OVER (PARTITION BY month ORDER BY total_revenue DESC) AS monthly_vendor_rank
FROM monthly_vendor_revenue
ORDER BY vendor_name, month;
