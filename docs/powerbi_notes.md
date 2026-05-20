# Power BI Notes

Use Power BI as the visualization layer. The recommended inputs are the exported OLAP CSV files in `output/`.

## Import Data

Import these CSVs:

- `output/result_q2.csv`
- `output/result_q4.csv`
- `output/result_q7.csv`
- `output/result_q9.csv`
- `output/result_q10.csv`

The other exported CSVs can be imported if extra report tables are needed.

## Required Visuals

| Visual | Source CSV | Suggested Power BI visual |
|---|---|---|
| Revenue by month | `result_q2.csv` | Clustered column chart |
| Weekday vs weekend demand by hour | `result_q7.csv` | Line chart |
| Top 10 pickup zones | `result_q9.csv` | Horizontal bar chart |
| Tip percentage by payment type | `result_q10.csv` | Bar chart or pie chart |
| Average trip duration by borough | `result_q4.csv` | Bar chart |
| Hour by day-of-week demand | `result_q7.csv` | Matrix with conditional formatting |

## Exported Images

Export chart images or dashboard screenshots to `output/charts/` with these names:

- `01_revenue_by_month.png`
- `02_demand_by_hour.png`
- `03_top10_zones.png`
- `04_tip_by_payment.png`
- `05_duration_by_borough.png`
- `06_heatmap_hour_dow.png`

## Optional Direct Database Connection

Power BI can also connect directly to PostgreSQL:

```text
Host: localhost
Port: 5433
Database: nyc_taxi_dw
Username: taxi
Password: taxi
```

Use the database connection only for extra exploration. The exported OLAP CSVs are the reproducible inputs for the required charts.
