from generate_synthetic_data import main as generate
from init_duckdb import main as init_db


if __name__ == "__main__":
    generate()
    init_db()
