from backend.app.services.analytics import analyze_sparse_product


def test_new_product_confidence_is_capped():
    result = analyze_sparse_product("P020")
    assert result["history_days"] <= 30
    assert result["evidence_confidence_cap"] <= 0.60
