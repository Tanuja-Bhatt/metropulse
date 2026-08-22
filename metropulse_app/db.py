from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
# DATABASE_PATH = PROJECT_ROOT / "data" / "metropulse.duckdb"
DATABASE_PATH = PROJECT_ROOT / "data" / "metropulse_deploy.duckdb"

def get_connection() -> duckdb.DuckDBPyConnection:
    """
    Open a read-only DuckDB connection to the MetroPulse warehouse.

    The Streamlit application is intentionally read-only:
    analytical transformations belong in the warehouse/marts,
    not in the presentation layer.
    """
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"MetroPulse DuckDB database not found at: {DATABASE_PATH}"
        )

    return duckdb.connect(str(DATABASE_PATH), read_only=True)


def execute_query(query: str):
    """
    Execute a SQL query and return the result as a pandas DataFrame.
    """
    connection = get_connection()

    try:
        return connection.execute(query).df()
    finally:
        connection.close()