# Validation Summary

This file records the main checks used to verify that the ETL and warehouse load are consistent.

## Raw Data

| File | Rows |
|---|---:|
| `yellow_tripdata_2024-01.parquet` | 2,964,624 |
| `yellow_tripdata_2024-02.parquet` | 3,007,526 |
| `yellow_tripdata_2024-03.parquet` | 3,582,628 |
| **Total raw** | **9,554,778** |

## Clean Data

| File | Rows kept | Rows dropped |
|---|---:|---:|
| January 2024 | 2,713,591 | 251,033 |
| February 2024 | 2,709,891 | 297,635 |
| March 2024 | 3,024,564 | 558,064 |
| **Total clean** | **8,448,046** | **1,106,732** |

Cleaned pickup timestamps were verified to fall inside January-March 2024.

## Loaded Warehouse Counts

| Table | Rows |
|---|---:|
| `dim_payment` | 6 |
| `dim_service` | 2 |
| `dim_pickup_location` | 265 |
| `dim_dropoff_location` | 265 |
| `dim_time` | 2,183 |
| `fact_trip` | 8,448,046 |

`dim_time` covers `2024-01-01` through `2024-03-31`, with hours `0-23`.

## OLAP Export Counts

| File | Data rows |
|---|---:|
| `result_q1.csv` | 2,278 |
| `result_q2.csv` | 5 |
| `result_q3.csv` | 257 |
| `result_q4.csv` | 7 |
| `result_q5.csv` | 31 |
| `result_q6.csv` | 3 |
| `result_q7.csv` | 168 |
| `result_q8.csv` | 20 |
| `result_q9.csv` | 10 |
| `result_q10.csv` | 4 |
| `result_q11.csv` | 159 |
| `result_q12.csv` | 6 |

## Useful Verification Commands

```bash
docker compose ps
docker exec -it nyc_taxi_postgres psql -U taxi -d nyc_taxi_dw -c "\dt"
docker exec -it nyc_taxi_postgres psql -U taxi -d nyc_taxi_dw -c "SELECT COUNT(*) FROM fact_trip;"
python etl/export_olap_results.py
```
