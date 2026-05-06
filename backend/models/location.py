from sqlalchemy import String, Numeric, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Location(Base):
    __tablename__ = "location"

    location_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    event_id: Mapped[str | None] = mapped_column(ForeignKey("event.event_id"))
    country: Mapped[str | None] = mapped_column(String(100))
    state_province: Mapped[str | None] = mapped_column(String(100))
    county: Mapped[str | None] = mapped_column(String(100))
    municipality: Mapped[str | None] = mapped_column(String(100))
    locality: Mapped[str | None] = mapped_column(Text)
    decimal_latitude: Mapped[float | None] = mapped_column(Numeric(10, 7))
    decimal_longitude: Mapped[float | None] = mapped_column(Numeric(10, 7))
    geodetic_datum: Mapped[str | None] = mapped_column(String(20), default="WGS84")
    coordinate_uncertainty: Mapped[float | None] = mapped_column(Numeric(10, 2))
    minimum_elevation: Mapped[float | None] = mapped_column(Numeric(8, 2))
    verbatim_coordinates: Mapped[str | None] = mapped_column(String(200))

    event: Mapped["Event | None"] = relationship(back_populates="locations")
    occurrences: Mapped[list["Occurrence"]] = relationship(back_populates="location")
