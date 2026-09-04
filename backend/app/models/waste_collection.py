from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class WasteCollection(Base):
    __tablename__ = "waste_collections"
    __table_args__ = (
        CheckConstraint("waste_tons >= 0", name="check_non_negative_waste_collection"),
    )

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id", ondelete="CASCADE"), nullable=False, index=True)
    stop_id = Column(Integer, ForeignKey("route_stops.id", ondelete="SET NULL"), nullable=True, index=True)
    collection_date = Column(Date, default=date.today, index=True, nullable=False)
    waste_tons = Column(Float, nullable=False)
    waste_type = Column(String(50), default="GENERAL", nullable=False)  # GENERAL, RECYCLABLE, ORGANIC, MIXED
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    route = relationship("Route", back_populates="waste_collections")
    stop = relationship("RouteStop", back_populates="waste_collections")
