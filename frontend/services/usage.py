from datetime import date
from typing import Any, Dict, Optional
from services.client import api_request
from state.adapter import get_household_id


def fetch_usage_summary(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> Dict[str, Any]:
    household_id = get_household_id()
    if not household_id:
        return {
            "logs": [],
            "most_used": [],
            "least_used": [],
            "period_from": None,
            "period_to": None,
        }

    params: Dict[str, Any] = {"household_id": household_id}
    if from_date:
        params["from_date"] = from_date.isoformat()
    if to_date:
        params["to_date"] = to_date.isoformat()

    return api_request("get", "/usage", params=params)
