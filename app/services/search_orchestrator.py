from __future__ import annotations

import asyncio
import logging

from app.config import Settings, get_settings
from app.models import ProductOffer
from app.providers.registry import get_provider_clients, get_provider_map
from app.schemas import ProductOfferData, ProviderAvailability, SearchResponse

logger = logging.getLogger(__name__)


class SearchOrchestrator:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.providers = get_provider_clients(self.settings)

    async def search(self, query: str) -> SearchResponse:
        statuses = [provider.availability() for provider in self.providers]

        supported_providers = [
            provider
            for provider, status in zip(self.providers, statuses)
            if status.supported
        ]

        offers: list[ProductOfferData] = []
        if not supported_providers:
            return SearchResponse(query=query, offers=offers, statuses=statuses)

        tasks = [
            provider.search(
                query,
                max_results=self.settings.search_max_results_per_provider,
                timeout_seconds=self.settings.search_timeout_seconds,
            )
            for provider in supported_providers
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        status_map: dict[str, ProviderAvailability] = {
            status.provider: status for status in statuses
        }

        for provider, result in zip(supported_providers, results):
            if isinstance(result, Exception):
                logger.exception("Provider %s failed during search", provider.name)
                status_map[provider.name] = ProviderAvailability(
                    provider=provider.name,
                    label=provider.label,
                    supported=False,
                    reason=f"Search failed: {type(result).__name__}",
                )
                continue
            offers.extend(result)

        offers.sort(key=lambda offer: offer.price)

        ordered_statuses = [status_map[provider.name] for provider in self.providers]
        return SearchResponse(query=query, offers=offers, statuses=ordered_statuses)

    async def refresh_offer(self, offer: ProductOffer) -> ProductOfferData | None:
        provider = get_provider_map(self.settings).get(offer.provider)
        if provider is None:
            return None

        availability = provider.availability()
        if not availability.supported:
            return None

        try:
            return await provider.refresh_offer(
                offer,
                timeout_seconds=self.settings.search_timeout_seconds,
            )
        except Exception:
            logger.exception("Provider %s failed while refreshing offer %s", offer.provider, offer.offer_id)
            return None
