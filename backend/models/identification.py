from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Identification(Base):
    __tablename__ = "identification"

    identification_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    occurrence_id: Mapped[str] = mapped_column(ForeignKey("occurrence.occurrence_id"), nullable=False)
    taxon_id: Mapped[str | None] = mapped_column(ForeignKey("taxon.taxon_id"))
    identified_by: Mapped[str | None] = mapped_column(String(300))
    date_identified: Mapped[str | None] = mapped_column(String(20))
    identification_remarks: Mapped[str | None] = mapped_column(Text)
    identification_qualifier: Mapped[str | None] = mapped_column(String(50))
    verification_status: Mapped[str] = mapped_column(String(20), default="unverified")

    occurrence: Mapped["Occurrence"] = relationship(back_populates="identifications")
    taxon: Mapped["Taxon | None"] = relationship(back_populates="identifications")
