from functools import lru_cache
import yaml
from backend.app.config import settings


@lru_cache(maxsize=1)
def load_contracts() -> dict:
    path = settings.root_dir / "backend" / "app" / "knowledge" / "kpi_contracts.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def get_contract(kpi: str) -> dict:
    contracts = load_contracts()
    if kpi not in contracts:
        raise KeyError(f"Unknown KPI: {kpi}")
    return contracts[kpi]
