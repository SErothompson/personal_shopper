from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote

import httpx

from app.models import ProductOffer
from app.providers.base import ProviderClient, build_offer_id
from app.schemas import ProductOfferData, ProviderAvailability


class BestBuyProvider(ProviderClient):
    name = "bestbuy"
    label = "Best Buy"

    def availability(self) -> ProviderAvailability:
        if not self.settings.bestbuy_api_key:
            return ProviderAvailability(
                provider=self.name,
                label=self.label,
                supported=False,
                reason="Set BESTBUY_API_KEY to enable official Best Buy API search.",
            )
        return ProviderAvailability(provider=self.name, label=self.label, supported=True)

    async def search(
        self,
        query: str,
        *,
        max_results: int,
        timeout_seconds: float,
    ) -> list[ProductOfferData]:
        if not self.settings.bestbuy_api_key:
            return []

        encoded_query = quote(query)
        endpoint = f"https://api.bestbuy.com/v1/products((search={encoded_query}*))"

        params = {
            "apiKey": self.settings.bestbuy_api_key,
            "format": "json",
            "show": "sku,name,salePrice,regularPrice,shortDescription,longDescription,image,url",
            "sort": "salePrice.asc",
            "pageSize": str(max_results),
        }

        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            payload = response.json()

        raw_products = payload.get("products", [])
        offers: list[ProductOfferData] = []
        for product in raw_products:
            sku = product.get("sku")
            title = product.get("name") or "Best Buy listing"
            product_url = product.get("url") or ""
            if not product_url:
                continue

            price = product.get("salePrice")
            if price is None:
                price = product.get("regularPrice")

            try:
                final_price = round(float(price), 2)
            except (TypeError, ValueError):
                continue

            offers.append(
                ProductOfferData(
                    offer_id=build_offer_id(self.name, str(sku) if sku else None, product_url),
                    query=query,
                    provider=self.name,
                    provider_label=self.label,
                    external_id=str(sku) if sku else None,
                    title=title,
                    description=(product.get("longDescription") or product.get("shortDescription") or title),
                    image_url=product.get("image"),
                    extra_images=[],
                    price=final_price,
                    currency="USD",
                    product_url=product_url,
                    fetched_at=datetime.now(timezone.utc),
                )
            )

        return offers

    async def refresh_offer(
        self,
        offer: ProductOffer,
        *,
        timeout_seconds: float,
    ) -> ProductOfferData | None:
        if not self.settings.bestbuy_api_key or not offer.external_id:
            return None

        endpoint = f"https://api.bestbuy.com/v1/products(sku={offer.external_id})"
        params = {
            "apiKey": self.settings.bestbuy_api_key,
            "format": "json",
            "show": "sku,name,salePrice,regularPrice,shortDescription,longDescription,image,url",
            "pageSize": "1",
        }

        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            payload = response.json()

        products = payload.get("products", [])
        if not products:
            return None

        product = products[0]
        price = product.get("salePrice")
        if price is None:
            price = product.get("regularPrice")

        try:
            final_price = round(float(price), 2)
        except (TypeError, ValueError):
            final_price = offer.price

        title = product.get("name") or offer.title
        description = product.get("longDescription") or product.get("shortDescription") or offer.description

        return ProductOfferData(
            offer_id=offer.offer_id,
            query=offer.query,
            provider=offer.provider,
            provider_label=offer.provider_label,
            external_id=offer.external_id,
            title=title,
            description=description,
            image_url=product.get("image") or offer.image_url,
            extra_images=[],
            price=final_price,
            currency=offer.currency,
            product_url=product.get("url") or offer.product_url,
            fetched_at=datetime.now(timezone.utc),
        )
