from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod

from app.config import Settings
from app.models import ProductOffer
from app.schemas import ProductOfferData, ProviderAvailability


class ProviderClient(ABC):
    name = "base"
    label = "Base Provider"

    def __init__(self, settings: Settings):
        self.settings = settings

    def availability(self) -> ProviderAvailability:
        return ProviderAvailability(provider=self.name, label=self.label, supported=True)

    @abstractmethod
    async def search(
        self,
        query: str,
        *,
        max_results: int,
        timeout_seconds: float,
    ) -> list[ProductOfferData]:
        raise NotImplementedError

    async def refresh_offer(
        self,
        offer: ProductOffer,
        *,
        timeout_seconds: float,
    ) -> ProductOfferData | None:
        return None


def build_offer_id(provider: str, external_id: str | None, product_url: str) -> str:
    source = f"{provider}|{external_id or product_url}".encode("utf-8")
    digest = hashlib.sha1(source).hexdigest()
    return f"{provider}-{digest[:20]}"
