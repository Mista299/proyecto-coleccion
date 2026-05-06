from sqlalchemy import String, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Event(Base):
    __tablename__ = "event"

    event_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    event_date: Mapped[str | None] = mapped_column(String(20))
    year: Mapped[int | None] = mapped_column()
    month: Mapped[int | None] = mapped_column()
    day: Mapped[int | None] = mapped_column()
    habitat: Mapped[str | None] = mapped_column(String(300))
    sampling_protocol: Mapped[str | None] = mapped_column(String(200))

    locations: Mapped[list["Location"]] = relationship(back_populates="event")
    occurrences: Mapped[list["Occurrence"]] = relationship(back_populates="event")
