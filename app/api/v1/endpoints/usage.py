"""Usage/consumption tracking endpoint."""

from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.usage_log import ItemUsageLog
from app.schemas.usage import UsageItemSummary, UsageSummaryResponse

router = APIRouter()


@router.get("", response_model=UsageSummaryResponse)
def get_usage_summary(
    household_id: int = Query(..., description="Household ID"),
    from_date: Optional[date] = Query(None, description="Start date (inclusive, YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, description="End date (inclusive, YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get consumption summary for a household over an optional date range.

    - **household_id**: The household to query
    - **from_date**: Start of range (inclusive)
    - **to_date**: End of range (inclusive)
    """
    if current_user.household_id != household_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this household",
        )

    query = db.query(
        ItemUsageLog.item_name,
        ItemUsageLog.unit,
        func.sum(ItemUsageLog.quantity_consumed).label("total_consumed"),
        func.max(ItemUsageLog.consumed_at).label("last_consumed"),
    ).filter(ItemUsageLog.household_id == household_id)

    if from_date:
        from_dt = datetime(from_date.year, from_date.month, from_date.day, tzinfo=timezone.utc)
        query = query.filter(ItemUsageLog.consumed_at >= from_dt)

    if to_date:
        to_dt = datetime(to_date.year, to_date.month, to_date.day, tzinfo=timezone.utc) + timedelta(
            days=1
        )
        query = query.filter(ItemUsageLog.consumed_at < to_dt)

    rows = query.group_by(ItemUsageLog.item_name, ItemUsageLog.unit).all()

    logs = [
        UsageItemSummary(
            item_name=r.item_name,
            unit=r.unit,
            total_consumed=r.total_consumed,
            last_consumed=r.last_consumed,
        )
        for row in rows
    ]

    sorted_logs = sorted(logs, key=lambda x: x.total_consumed, reverse=True)
    most_used = sorted_logs[:3]
    least_used = (
        list(reversed(sorted_logs[-3:])) if len(sorted_logs) >= 3 else list(reversed(sorted_logs))
    )

    return UsageSummaryResponse(
        logs=sorted_logs,
        most_used=most_used,
        least_used=least_used,
        period_from=from_date,
        period_to=to_date,
    )
