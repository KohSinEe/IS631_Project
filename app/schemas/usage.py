"""Schemas for usage/consumption tracking."""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


class UsageItemSummary(BaseModel):
    item_name: str
    unit: str
    total_consumed: int
    last_consumed: datetime


class UsageSummaryResponse(BaseModel):
    logs: List[UsageItemSummary]
    most_used: List[UsageItemSummary]
    least_used: List[UsageItemSummary]
    period_from: Optional[date] = None
    period_to: Optional[date] = None
