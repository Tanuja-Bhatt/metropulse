from metropulse_app.db import execute_query


def get_executive_metrics():
    query = """
        SELECT *
        FROM marts.executive_mobility
    """
    return execute_query(query)


def get_temporal_demand():
    query = """
        SELECT *
        FROM marts.temporal_demand
        ORDER BY pickup_hour
    """
    return execute_query(query)


def get_geographic_performance():
    query = """
        SELECT *
        FROM marts.geographic_performance
        ORDER BY activity_rank
    """
    return execute_query(query)


def get_fare_payment_analysis():
    query = """
        SELECT *
        FROM marts.fare_payment_analysis
        ORDER BY total_amount DESC
    """
    return execute_query(query)


def get_weather_transit_analysis():
    query = """
        SELECT *
        FROM marts.weather_transit_analysis
        ORDER BY pickup_hour
    """
    return execute_query(query)


def get_statistical_analysis():
    query = """
        SELECT *
        FROM marts.statistical_analysis
        ORDER BY pickup_hour
    """
    return execute_query(query)


def get_data_quality_anomalies():
    query = """
        SELECT *
        FROM marts.data_quality_anomalies
        ORDER BY
            CASE severity
                WHEN 'Critical' THEN 1
                WHEN 'High' THEN 2
                WHEN 'Medium' THEN 3
                WHEN 'Low' THEN 4
                ELSE 5
            END,
            affected_rows DESC
    """
    return execute_query(query)