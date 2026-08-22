import duckdb
from pathlib import Path
import re

DB_PATH = Path("data/metropulse.duckdb")
OUTPUT_PATH = Path("outputs/query_optimization_benchmarks.csv")

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

con = duckdb.connect(str(DB_PATH), read_only=True)

benchmarks = [
    (
        "Payment analysis",
        "Before",
        """
        SELECT
            payment_type,
            COUNT(*) AS trips,
            SUM(total_amount) AS total_amount,
            AVG(total_amount) AS avg_amount,
            MEDIAN(total_amount) AS median_amount,
            AVG(tip_percentage) AS avg_tip_percentage
        FROM intermediate.trip_metrics
        GROUP BY payment_type
        """,
    ),
    (
        "Payment analysis",
        "After",
        """
        SELECT
            payment_type,
            trips,
            total_amount,
            avg_amount,
            median_amount,
            avg_tip_percentage
        FROM marts.fare_payment_analysis
        """,
    ),
    (
        "Geographic analysis",
        "Before",
        """
        SELECT
            pickup_location_id AS location_id,
            COUNT(*) AS pickup_trips,
            SUM(total_amount) AS pickup_revenue,
            AVG(trip_distance) AS avg_pickup_distance,
            AVG(trip_duration_minutes) AS avg_pickup_duration_minutes
        FROM intermediate.trip_metrics
        GROUP BY pickup_location_id
        """,
    ),
    (
        "Geographic analysis",
        "After",
        """
        SELECT
            location_id,
            pickup_trips,
            pickup_revenue,
            avg_pickup_distance,
            avg_pickup_duration_minutes
        FROM marts.geographic_performance
        """,
    ),
]


def get_total_time_ms(query):
    rows = con.execute(f"EXPLAIN ANALYZE {query}").fetchall()

    text = "\n".join(str(row) for row in rows)

    match = re.search(
        r"Total Time:\s*([0-9.]+)s",
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        raise RuntimeError(
            "Could not extract Total Time from EXPLAIN ANALYZE output."
        )

    return float(match.group(1)) * 1000


results = []

for name, version, query in benchmarks:

    # Run multiple times and use the median to reduce noise.
    timings = []

    for _ in range(5):
        timings.append(get_total_time_ms(query))

    timings.sort()

    median_ms = timings[len(timings) // 2]

    results.append(
        {
            "analysis": name,
            "version": version,
            "median_execution_ms": median_ms,
            "repetitions": 5,
        }
    )


# Calculate improvement for each optimization.
for analysis in ["Payment analysis", "Geographic analysis"]:

    before = next(
        row["median_execution_ms"]
        for row in results
        if row["analysis"] == analysis
        and row["version"] == "Before"
    )

    after = next(
        row["median_execution_ms"]
        for row in results
        if row["analysis"] == analysis
        and row["version"] == "After"
    )

    improvement = (
        100.0 * (before - after) / before
        if before > 0
        else None
    )

    for row in results:
        if row["analysis"] == analysis:
            row["improvement_pct"] = improvement


import csv

with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:

    writer = csv.DictWriter(
        f,
        fieldnames=[
            "analysis",
            "version",
            "median_execution_ms",
            "repetitions",
            "improvement_pct",
        ],
    )

    writer.writeheader()
    writer.writerows(results)


print("\nQUERY OPTIMIZATION BENCHMARKS")
print("=" * 70)

for row in results:
    print(
        f"{row['analysis']:25} "
        f"{row['version']:8} "
        f"{row['median_execution_ms']:12.3f} ms"
    )

print("\nSaved:")
print(OUTPUT_PATH)

con.close()