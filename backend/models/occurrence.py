from sqlalchemy import String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from database import Base


class Occurrence(Base):
    __tablename__ = "occurrence"

    occurrence_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    basis_of_record: Mapped[str] = mapped_column(String(50), default="PreservedSpecimen")
    institution_code: Mapped[str | None] = mapped_column(String(20))
    collection_code: Mapped[str | None] = mapped_column(String(20))
    catalog_number: Mapped[str | None] = mapped_column(String(50))
    occurrence_status: Mapped[str | None] = mapped_column(String(20), default="present")
    disposition: Mapped[str | None] = mapped_column(String(50))
    preparations: Mapped[str | None] = mapped_column(String(200))
    sex: Mapped[str | None] = mapped_column(String(20))
    individual_count: Mapped[int | None] = mapped_column()
    life_stage: Mapped[str | None] = mapped_column(String(50))
    occurrence_remarks: Mapped[str | None] = mapped_column(Text)
    recorded_by: Mapped[str | None] = mapped_column(String(300))
    field_number: Mapped[str | None] = mapped_column(String(100))
    source_file: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[str | None] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[str | None] = mapped_column(DateTime, onupdate=func.now())

    event_id: Mapped[str | None] = mapped_column(ForeignKey("event.event_id"))
    taxon_id: Mapped[str | None] = mapped_column(ForeignKey("taxon.taxon_id"))
    location_id: Mapped[str | None] = mapped_column(ForeignKey("location.location_id"))

    event: Mapped["Event | None"] = relationship(back_populates="occurrences")
    taxon: Mapped["Taxon | None"] = relationship(back_populates="occurrences")
    location: Mapped["Location | None"] = relationship(back_populates="occurrences")
    identifications: Mapped[list["Identification"]] = relationship(back_populates="occurrence")
