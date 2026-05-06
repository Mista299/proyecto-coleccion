from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Taxon(Base):
    __tablename__ = "taxon"

    taxon_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    scientific_name: Mapped[str] = mapped_column(String(300), nullable=False)
    taxon_rank: Mapped[str | None] = mapped_column(String(30))
    kingdom: Mapped[str | None] = mapped_column(String(100))
    phylum: Mapped[str | None] = mapped_column(String(100))
    class_: Mapped[str | None] = mapped_column("class", String(100))
    order: Mapped[str | None] = mapped_column(String(100))
    family: Mapped[str | None] = mapped_column(String(100))
    genus: Mapped[str | None] = mapped_column(String(100))
    specific_epithet: Mapped[str | None] = mapped_column(String(100))
    taxon_remarks: Mapped[str | None] = mapped_column(Text)

    occurrences: Mapped[list["Occurrence"]] = relationship(back_populates="taxon")
    identifications: Mapped[list["Identification"]] = relationship(back_populates="taxon")
