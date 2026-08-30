import sys
import json
from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.services.analytics import analyze_kpi, analyze_sparse_product

META = ROOT / "data" / "metadata"


def main() -> None:
    main_result = analyze_kpi("North", "revenue", "main")
    degraded = analyze_kpi("North", "revenue", "degraded")
    sparse = analyze_sparse_product("P020")
    truth = pd.read_csv(META / "ground_truth_drivers.csv").to_dict(orient="records")

    snapshot = {
        "main_demo": {
            "delta_pct": round(main_result["delta_pct"], 3),
            "anomaly_score": round(main_result["anomaly_score"], 3),
            "materiality_score": round(main_result["materiality_score"], 3),
            "evidence_confidence_score": round(main_result["ecs"], 3),
            "confidence_band": main_result["band"],
            "bridge": main_result["bridge"],
            "diagnoses": main_result["diagnoses"],
        },
        "degraded_demo": {
            "evidence_confidence_score": round(degraded["ecs"], 3),
            "confidence_band": degraded["band"],
            "abstentions": degraded["abstentions"],
        },
        "sparse_history_demo": sparse,
        "synthetic_ground_truth": truth,
    }
    out = META / "evaluation_snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
