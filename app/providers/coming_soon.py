from app.models import ProductOffer
from app.providers.base import ProviderClient
from app.schemas import ProductOfferData, ProviderAvailability


class ComingSoonProvider(ProviderClient):
    def __init__(self, settings, *, name: str, label: str, reason: str):
        super().__init__(settings)
        self.name = name
        self.label = label
        self.reason = reason

    def availability(self) -> ProviderAvailability:
        return ProviderAvailability(
            provider=self.name,
            label=self.label,
            supported=False,
            reason=self.reason,
        )

    async def search(
        self,
        query: str,
        *,
        max_results: int,
        timeout_seconds: float,
    ) -> list[ProductOfferData]:
        return []

    async def refresh_offer(
        self,
        offer: ProductOffer,
        *,
        timeout_seconds: float,
    ) -> ProductOfferData | None:
        return None
