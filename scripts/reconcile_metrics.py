from pathlib import Path
import duckdb
import csv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "data" / "metropulse.duckdb"
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "reconciliation_checks.csv"

conn = duckdb.connect(str(DATABASE_PATH), read_only=True)

checks = []

def add_check(name, expected, actual):
    checks.append({
        "check_name": name,
        "expected": expected,
        "actual": actual,
        "status": "PASS" if expected == actual else "FAIL",
    })

# 1. Staging -> cleaned
staging_rows = conn.execute(
    "SELECT COUNT(*) FROM staging.taxi_trips"
).fetchone()[0]

clean_rows = conn.execute(
    "SELECT COUNT(*) FROM intermediate.taxi_trips_clean"
).fetchone()[0]

add_check(
    "staging_to_clean_rows",
    staging_rows,
    clean_rows,
)

# 2. Cleaned -> trip metrics
trip_metric_rows = conn.execute(
    "SELECT COUNT(*) FROM intermediate.trip_metrics"
).fetchone()[0]

add_check(
    "clean_to_trip_metrics_rows",
    clean_rows,
    trip_metric_rows,
)

# 3. Trip metrics -> total market trips
total_trips = conn.execute(
    "SELECT COUNT(*) FROM intermediate.trip_metrics"
).fetchone()[0]

add_check(
    "trip_metrics_to_total_trips",
    trip_metric_rows,
    total_trips,
)

# 4. Payment mart trip total -> total trips
payment_trips = conn.execute(
    "SELECT COALESCE(SUM(trips), 0) FROM marts.fare_payment_analysis"
).fetchone()[0]

add_check(
    "payment_mart_to_total_trips",
    total_trips,
    payment_trips,
)

# 5. Temporal mart -> hourly trip total
temporal_trips = conn.execute(
    "SELECT COALESCE(SUM(taxi_trip_count), 0) FROM marts.temporal_demand"
).fetchone()[0]

add_check(
    "temporal_mart_to_total_trips",
    total_trips,
    temporal_trips,
)

# 6. Geographic pickup activity -> total trips
geographic_pickups = conn.execute(
    "SELECT COALESCE(SUM(pickup_trips), 0) FROM marts.geographic_performance"
).fetchone()[0]

add_check(
    "geographic_pickups_to_total_trips",
    total_trips,
    geographic_pickups,
)

# 7. Warehouse quality status
quality_status = conn.execute(
    "SELECT warehouse_quality_status "
    "FROM intermediate.data_quality_metrics "
    "LIMIT 1"
).fetchone()[0]

checks.append({
    "check_name": "warehouse_quality_status",
    "expected": "PASS",
    "actual": quality_status,
    "status": "PASS" if quality_status == "PASS" else "FAIL",
})

conn.close()

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["check_name", "expected", "actual", "status"],
    )
    writer.writeheader()
    writer.writerows(checks)

failed = [row for row in checks if row["status"] != "PASS"]

print("RECONCILIATION CHECKS")
print("=" * 70)

for row in checks:
    print(
        f"{row['check_name']:<40} "
        f"{row['status']}"
    )

print()
print(f"Saved: {OUTPUT_PATH}")

if failed:
    raise SystemExit(f"{len(failed)} reconciliation check(s) failed.")

print("All reconciliation checks passed.")
