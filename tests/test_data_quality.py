from pathlib import Path

import duckdb
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "data" / "metropulse.duckdb"


@pytest.fixture(scope="module")
def db():
    assert DATABASE_PATH.exists(), f"DuckDB database not found: {DATABASE_PATH}"

    connection = duckdb.connect(str(DATABASE_PATH), read_only=True)

    yield connection

    connection.close()


def scalar(db, query):
    return db.execute(query).fetchone()[0]


def test_warehouse_quality_status_is_pass(db):
    status = scalar(
        db,
        """
        SELECT warehouse_quality_status
        FROM intermediate.data_quality_metrics
        LIMIT 1
        """,
    )

    assert status == "PASS"


def test_core_trip_row_reconciliation(db):
    row = db.execute(
        """
        SELECT
            staging_taxi_rows,
            clean_taxi_rows,
            trip_metric_rows,
            total_trips
        FROM intermediate.data_quality_metrics
        LIMIT 1
        """
    ).fetchone()

    staging_rows, clean_rows, metric_rows, total_trips = row

    assert staging_rows >= clean_rows
    assert clean_rows == metric_rows
    assert metric_rows == total_trips


def test_quality_percentages_are_bounded(db):
    columns = [
        "pickup_zone_completeness_pct",
        "dropoff_zone_completeness_pct",
        "duration_validity_pct",
        "distance_validity_pct",
        "revenue_validity_pct",
        "passenger_validity_pct",
        "weather_completeness_pct",
        "subway_completeness_pct",
    ]

    expression = ", ".join(columns)

    values = db.execute(
        f"""
        SELECT {expression}
        FROM intermediate.data_quality_metrics
        LIMIT 1
        """
    ).fetchone()

    for value in values:
        assert value is not None
        assert 0 <= value <= 100


def test_trip_metric_grain_is_unique(db):
    duplicates = scalar(
        db,
        """
        SELECT COUNT(*)
        FROM (
            SELECT
                pickup_datetime,
                dropoff_datetime,
                pickup_location_id,
                dropoff_location_id,
                total_amount
            FROM intermediate.trip_metrics
            GROUP BY
                pickup_datetime,
                dropoff_datetime,
                pickup_location_id,
                dropoff_location_id,
                total_amount
            HAVING COUNT(*) > 1
        )
        """,
    )

    assert duplicates == 0


def test_geographic_location_ids_are_unique(db):
    duplicate_locations = scalar(
        db,
        """
        SELECT COUNT(*)
        FROM (
            SELECT location_id
            FROM marts.geographic_performance
            GROUP BY location_id
            HAVING COUNT(*) > 1
        )
        """,
    )

    assert duplicate_locations == 0


def test_geographic_activity_is_non_negative(db):
    invalid_rows = scalar(
        db,
        """
        SELECT COUNT(*)
        FROM marts.geographic_performance
        WHERE pickup_trips < 0
           OR dropoff_trips < 0
           OR total_zone_activity < 0
           OR total_zone_revenue < 0
        """,
    )

    assert invalid_rows == 0


def test_temporal_demand_has_unique_hourly_grain(db):
    duplicate_hours = scalar(
        db,
        """
        SELECT COUNT(*)
        FROM (
            SELECT
                pickup_hour
            FROM marts.temporal_demand
            GROUP BY pickup_hour
            HAVING COUNT(*) > 1
        )
        """,
    )

    assert duplicate_hours == 0


def test_temporal_demand_has_valid_hours(db):
    invalid_hours = scalar(
        db,
        """
        SELECT COUNT(*)
        FROM marts.temporal_demand
        WHERE hour_of_day < 0
           OR hour_of_day > 23
        """,
    )

    assert invalid_hours == 0


def test_payment_analysis_reconciles_to_trip_total(db):
    payment_trips = scalar(
        db,
        """
        SELECT SUM(trips)
        FROM marts.fare_payment_analysis
        """
    )

    total_trips = scalar(
        db,
        """
        SELECT total_trips
        FROM intermediate.data_quality_metrics
        LIMIT 1
        """
    )

    assert payment_trips == total_trips


def test_weather_transit_analysis_has_valid_hourly_grain(db):
    duplicate_hours = scalar(
        db,
        """
        SELECT COUNT(*)
        FROM (
            SELECT pickup_hour
            FROM marts.weather_transit_analysis
            GROUP BY pickup_hour
            HAVING COUNT(*) > 1
        )
        """
    )

    assert duplicate_hours == 0