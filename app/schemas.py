from datetime import datetime, timezone

from pydantic import BaseModel, Field


class ProductOfferData(BaseModel):
    offer_id: str
    query: str
    provider: str
    provider_label: str
    external_id: str | None = None
    title: str
    description: str
    image_url: str | None = None
    extra_images: list[str] = Field(default_factory=list)
    price: float
    currency: str = "USD"
    product_url: str
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProviderAvailability(BaseModel):
    provider: str
    label: str
    supported: bool
    reason: str | None = None


class SearchResponse(BaseModel):
    query: str
    offers: list[ProductOfferData] = Field(default_factory=list)
    statuses: list[ProviderAvailability] = Field(default_factory=list)
