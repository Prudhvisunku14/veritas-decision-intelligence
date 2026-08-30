from dataclasses import dataclass
from fastapi import Header, HTTPException


@dataclass(frozen=True)
class DemoUser:
    user_id: str
    role: str
    regions: tuple[str, ...]
    kpis: tuple[str, ...]


ALL_KPIS = ("revenue", "orders", "conversion_rate", "aov", "gross_margin")

USERS = {
    "ceo": DemoUser("ceo", "ceo", ("ALL",), ALL_KPIS),
    "north_mgr": DemoUser("north_mgr", "regional_manager", ("North",), ALL_KPIS),
    "marketing_mgr": DemoUser(
        "marketing_mgr",
        "marketing_manager",
        ("ALL",),
        ("revenue", "orders", "conversion_rate", "aov"),
    ),
    "analyst": DemoUser("analyst", "analyst", ("ALL",), ALL_KPIS),
}


def get_demo_user(x_demo_user: str = Header(default="ceo")) -> DemoUser:
    user = USERS.get(x_demo_user)
    if not user:
        raise HTTPException(status_code=401, detail="Unknown demo user")
    return user


def authorize(user: DemoUser, region: str, kpi: str) -> None:
    if kpi not in user.kpis:
        raise HTTPException(status_code=403, detail=f"Role {user.role} cannot access KPI {kpi}")
    if "ALL" not in user.regions and region not in user.regions:
        raise HTTPException(
            status_code=403,
            detail=f"User {user.user_id} is authorized for {', '.join(user.regions)} only",
        )
