"""Invitation model for household (fridge) sharing."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import HouseholdRoleEnum, InvitationStatusEnum


class Invitation(Base):
    """Invitation to join a household with a specific role."""

    __tablename__ = "invitations"

    id = Column(Integer, primary_key=True, index=True)
    household_id = Column(Integer, ForeignKey("households.id"), nullable=False, index=True)
    inviter_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    invitee_email = Column(String(255), nullable=False, index=True)
    role = Column(Enum(HouseholdRoleEnum), nullable=False)
    status = Column(
        Enum(InvitationStatusEnum), nullable=False, default=InvitationStatusEnum.PENDING
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    household = relationship("Household", backref="invitations")
    inviter = relationship("User", foreign_keys=[inviter_id])

    def __repr__(self):
        return f"<Invitation(id={self.id}, household_id={self.household_id}, invitee_email='{self.invitee_email}', status='{self.status}')>"
