"""Generate reproducible analytical figures from the PostgreSQL warehouse."""

import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import psycopg2


ROOT = Path(__file__).resolve().parent.parent
FIGURES_DIR = ROOT / "docs" / "figures"
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5433")),
    "dbname": os.getenv("DB_NAME", "nyc_taxi_dw"),
    "user": os.getenv("DB_USER", "taxi"),
    "password": os.getenv("DB_PASSWORD", "taxi"),
}

COLORS = {
    "navy": "#172033",
    "blue": "#3976C5",
    "teal": "#159A8A",
    "orange": "#CA7B17",
    "coral": "#D95D50",
    "purple": "#8560BD",
    "grid": "#D8E0E8",
}


def query_dataframe(conn, query):
    with conn.cursor() as cursor:
        cursor.execute(query)
        columns = [column.name for column in cursor.description]
        return pd.DataFrame(cursor.fetchall(), columns=columns)


def style_axis(axis):
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.spines["left"].set_color(COLORS["grid"])
    axis.spines["bottom"].set_color(COLORS["grid"])
    axis.grid(axis="x", color=COLORS["grid"], linewidth=0.8)
    axis.set_axisbelow(True)


def save_figure(figure, filename):
    figure.tight_layout()
    figure.savefig(FIGURES_DIR / filename, dpi=180, bbox_inches="tight")
    plt.close(figure)


def pickup_hubs(conn):
    data = query_dataframe(
        conn,
        """
        SELECT l.zone, l.borough, COUNT(*) AS trip_count
        FROM fact_trip AS f
        JOIN dim_pickup_location AS l ON f.pickup_location_id = l.location_id
        GROUP BY l.zone, l.borough
        ORDER BY trip_count DESC
        LIMIT 10
        """,
    ).sort_values("trip_count")

    figure, axis = plt.subplots(figsize=(9.2, 5.5))
    labels = [f"{row.zone} ({row.borough})" for row in data.itertuples()]
    bars = axis.barh(labels, data["trip_count"] / 1000, color=COLORS["teal"])
    for bar, value in zip(bars, data["trip_count"]):
        axis.text(bar.get_width() + 4, bar.get_y() + bar.get_height() / 2, f"{value / 1000:.0f}k", va="center", color=COLORS["navy"], fontsize=9)
    axis.set_title("Top pickup hubs by trip volume", loc="left", color=COLORS["navy"], fontweight="bold")
    axis.set_xlabel("Trips (thousands)")
    axis.set_xlim(0, data["trip_count"].max() / 1000 + 65)
    style_axis(axis)
    save_figure(figure, "pickup_hubs.png")


def payment_mix(conn):
    data = query_dataframe(
        conn,
        """
        WITH top_zones AS (
            SELECT pickup_location_id
            FROM fact_trip
            GROUP BY pickup_location_id
            ORDER BY COUNT(*) DESC
            LIMIT 5
        )
        SELECT l.zone, p.payment_type, COUNT(*) AS trip_count
        FROM fact_trip AS f
        JOIN top_zones AS z ON f.pickup_location_id = z.pickup_location_id
        JOIN dim_pickup_location AS l ON f.pickup_location_id = l.location_id
        JOIN dim_payment AS p ON f.payment_id = p.payment_id
        GROUP BY l.zone, p.payment_type
        ORDER BY l.zone, p.payment_type
        """,
    )
    pivot = data.pivot(index="zone", columns="payment_type", values="trip_count").fillna(0)
    pivot = pivot.loc[pivot.sum(axis=1).sort_values().index]
    percentages = pivot.div(pivot.sum(axis=1), axis=0) * 100
    palette = [COLORS["blue"], COLORS["orange"], COLORS["purple"], COLORS["coral"], COLORS["teal"], "#9AA8B8"]

    figure, axis = plt.subplots(figsize=(9.2, 5.3))
    left = pd.Series(0, index=percentages.index, dtype=float)
    for color, payment_type in zip(palette, percentages.columns):
        axis.barh(percentages.index, percentages[payment_type], left=left, label=payment_type, color=color)
        left += percentages[payment_type]
    axis.set_title("Payment mix at the five busiest pickup hubs", loc="left", color=COLORS["navy"], fontweight="bold")
    axis.set_xlabel("Share of trips (%)")
    axis.set_xlim(0, 100)
    axis.legend(ncol=3, frameon=False, loc="lower center", bbox_to_anchor=(0.5, -0.31), fontsize=8)
    style_axis(axis)
    save_figure(figure, "payment_mix_top_zones.png")


def vendor_revenue(conn):
    data = query_dataframe(
        conn,
        """
        SELECT t.month, s.vendor_name, SUM(f.total_amount) AS total_revenue
        FROM fact_trip AS f
        JOIN dim_time AS t ON f.time_id = t.time_id
        JOIN dim_service AS s ON f.service_id = s.service_id
        GROUP BY t.month, s.vendor_name
        ORDER BY t.month, s.vendor_name
        """,
    )
    month_labels = {1: "Jan", 2: "Feb", 3: "Mar"}
    figure, axis = plt.subplots(figsize=(9.2, 5.3))
    for color, (vendor, rows) in zip([COLORS["blue"], COLORS["orange"]], data.groupby("vendor_name")):
        axis.plot(rows["month"], rows["total_revenue"] / 1_000_000, marker="o", linewidth=2.5, color=color, label=vendor)
    axis.set_title("Monthly revenue by vendor", loc="left", color=COLORS["navy"], fontweight="bold")
    axis.set_xlabel("Month in 2024")
    axis.set_ylabel("Revenue (million USD)")
    axis.set_xticks([1, 2, 3], [month_labels[month] for month in [1, 2, 3]])
    axis.legend(frameon=False, loc="upper left")
    axis.grid(axis="y", color=COLORS["grid"], linewidth=0.8)
    axis.set_axisbelow(True)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.spines["left"].set_color(COLORS["grid"])
    axis.spines["bottom"].set_color(COLORS["grid"])
    save_figure(figure, "vendor_revenue_by_month.png")


def hourly_demand(conn):
    data = query_dataframe(
        conn,
        """
        WITH daily_demand AS (
            SELECT t.pickup_date, t.hour, t.is_weekend, COUNT(*) AS trip_count
            FROM fact_trip AS f
            JOIN dim_time AS t ON f.time_id = t.time_id
            GROUP BY t.pickup_date, t.hour, t.is_weekend
        )
        SELECT hour, is_weekend, AVG(trip_count) AS avg_trip_count
        FROM daily_demand
        GROUP BY hour, is_weekend
        ORDER BY hour, is_weekend
        """,
    )
    figure, axis = plt.subplots(figsize=(9.2, 5.3))
    for color, label, is_weekend in [
        (COLORS["blue"], "Weekday", False),
        (COLORS["coral"], "Weekend", True),
    ]:
        rows = data[data["is_weekend"] == is_weekend]
        axis.plot(rows["hour"], rows["avg_trip_count"] / 1000, marker="o", markersize=3, linewidth=2.3, color=color, label=label)
    axis.set_title("Average daily taxi demand by pickup hour", loc="left", color=COLORS["navy"], fontweight="bold")
    axis.set_xlabel("Pickup hour")
    axis.set_ylabel("Average trips per day (thousands)")
    axis.set_xticks(range(0, 24, 2))
    axis.legend(frameon=False, loc="upper left")
    axis.grid(axis="y", color=COLORS["grid"], linewidth=0.8)
    axis.set_axisbelow(True)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.spines["left"].set_color(COLORS["grid"])
    axis.spines["bottom"].set_color(COLORS["grid"])
    save_figure(figure, "hourly_demand_by_day_type.png")


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    with psycopg2.connect(**DB_CONFIG) as conn:
        pickup_hubs(conn)
        payment_mix(conn)
        vendor_revenue(conn)
        hourly_demand(conn)
    print(f"Wrote figures to {FIGURES_DIR}")


if __name__ == "__main__":
    main()
