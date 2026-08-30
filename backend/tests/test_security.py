import pytest
from fastapi import HTTPException
from backend.app.security import USERS, authorize


def test_north_manager_denied_south():
    with pytest.raises(HTTPException) as exc:
        authorize(USERS["north_mgr"], "South", "revenue")
    assert exc.value.status_code == 403


def test_ceo_allowed_south():
    authorize(USERS["ceo"], "South", "revenue")
