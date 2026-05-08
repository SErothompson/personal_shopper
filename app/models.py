from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProductOffer(Base):
    __tablename__ = "product_offers"

    offer_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    query: Mapped[str] = mapped_column(String(300), index=True)
    provider: Mapped[str] = mapped_column(String(64), index=True)
    provider_label: Mapped[str] = mapped_column(String(120))
    external_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(600))
    description: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_images: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    price: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    product_url: Mapped[str] = mapped_column(Text)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)

    watched_items: Mapped[list["WatchedItem"]] = relationship(back_populates="offer")


class WatchedItem(Base):
    __tablename__ = "watched_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    offer_id: Mapped[str] = mapped_column(ForeignKey("product_offers.offer_id"), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_polled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    offer: Mapped[ProductOffer] = relationship(back_populates="watched_items")
    snapshots: Mapped[list["PriceSnapshot"]] = relationship(back_populates="watch", cascade="all, delete-orphan")


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    watch_id: Mapped[int] = mapped_column(ForeignKey("watched_items.id"), index=True)
    offer_id: Mapped[str] = mapped_column(String(80), index=True)
    provider: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(600))
    price: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    product_url: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)

    watch: Mapped[WatchedItem] = relationship(back_populates="snapshots")


Index("ix_price_snapshots_watch_captured", PriceSnapshot.watch_id, PriceSnapshot.captured_at)
