from backend.app.config import settings

try:
    import duckdb  # type: ignore
except ModuleNotFoundError:
    duckdb = None


def duckdb_available() -> bool:
    return duckdb is not None and settings.db_path.exists()


def connect(read_only: bool = False):
    if not duckdb_available():
        raise RuntimeError("DuckDB mode unavailable. Install requirements and run scripts/bootstrap.py.")
    return duckdb.connect(str(settings.db_path), read_only=read_only)


def ensure_data_available() -> None:
    gold = settings.root_dir / "data" / "gold" / "kpi_region_daily.csv"
    if not settings.db_path.exists() and not gold.exists():
        raise RuntimeError("Data not initialized. Run: python scripts/bootstrap.py")
