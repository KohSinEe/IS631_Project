"""ItemUsageLog model for tracking consumption history."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func

from app.database import Base


class ItemUsageLog(Base):
    """Records each consumption event when item quantity is decreased."""

    __tablename__ = "item_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="SET NULL"), nullable=True)
    item_name = Column(String(100), nullable=False)  # denormalized: preserved if item is deleted
    unit = Column(String(20), nullable=False)
    household_id = Column(
        Integer, ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quantity_consumed = Column(Integer, nullable=False)  # always positive (abs of change)
    consumed_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return (
            f"<ItemUsageLog(id={self.id}, item='{self.item_name}', qty={self.quantity_consumed})>"
        )
