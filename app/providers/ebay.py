from __future__ import annotations

from datetime import datetime, timezone

import httpx

from app.models import ProductOffer
from app.providers.base import ProviderClient, build_offer_id
from app.schemas import ProductOfferData, ProviderAvailability


def _first(value, default=None):
    if isinstance(value, list):
        if value:
            return value[0]
        return default
    return value if value is not None else default


class EbayProvider(ProviderClient):
    name = "ebay"
    label = "eBay"

    def availability(self) -> ProviderAvailability:
        if not self.settings.ebay_app_id:
            return ProviderAvailability(
                provider=self.name,
                label=self.label,
                supported=False,
                reason="Set EBAY_APP_ID to enable official eBay API search.",
            )
        return ProviderAvailability(provider=self.name, label=self.label, supported=True)

    async def search(
        self,
        query: str,
        *,
        max_results: int,
        timeout_seconds: float,
    ) -> list[ProductOfferData]:
        if not self.settings.ebay_app_id:
            return []

        params = {
            "OPERATION-NAME": "findItemsByKeywords",
            "SERVICE-VERSION": "1.0.0",
            "SECURITY-APPNAME": self.settings.ebay_app_id,
            "RESPONSE-DATA-FORMAT": "JSON",
            "REST-PAYLOAD": "true",
            "keywords": query,
            "paginationInput.entriesPerPage": str(max_results),
            "GLOBAL-ID": "EBAY-US",
            "sortOrder": "PricePlusShippingLowest",
        }

        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.get(
                "https://svcs.ebay.com/services/search/FindingService/v1",
                params=params,
            )
            response.raise_for_status()
            payload = response.json()

        raw_items = (
            _first(payload.get("findItemsByKeywordsResponse"), {})
            .get("searchResult", [{}])[0]
            .get("item", [])
        )

        offers: list[ProductOfferData] = []
        for item in raw_items:
            item_id = _first(item.get("itemId"))
            title = _first(item.get("title"), "Untitled listing")
            url = _first(item.get("viewItemURL"), "")
            image_url = _first(item.get("galleryURL"))

            selling_status = _first(item.get("sellingStatus"), {})
            price_info = _first((selling_status or {}).get("currentPrice"), {})
            shipping_info = _first(item.get("shippingInfo"), {})
            shipping_cost_info = _first((shipping_info or {}).get("shippingServiceCost"), {})

            try:
                base_price = float((price_info or {}).get("__value__", 0.0))
            except (TypeError, ValueError):
                base_price = 0.0

            try:
                shipping_price = float((shipping_cost_info or {}).get("__value__", 0.0))
            except (TypeError, ValueError):
                shipping_price = 0.0

            if not url:
                continue

            currency = (price_info or {}).get("@currencyId", "USD")
            total_price = round(base_price + shipping_price, 2)

            offers.append(
                ProductOfferData(
                    offer_id=build_offer_id(self.name, item_id, url),
                    query=query,
                    provider=self.name,
                    provider_label=self.label,
                    external_id=item_id,
                    title=title,
                    description=title,
                    image_url=image_url,
                    extra_images=[],
                    price=total_price,
                    currency=currency,
                    product_url=url,
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
        if not self.settings.ebay_app_id or not offer.external_id:
            return None

        params = {
            "callname": "GetSingleItem",
            "responseencoding": "JSON",
            "appid": self.settings.ebay_app_id,
            "siteid": "0",
            "version": "967",
            "ItemID": offer.external_id,
            "IncludeSelector": "Details",
        }

        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.get("https://open.api.ebay.com/shopping", params=params)
            response.raise_for_status()
            payload = response.json()

        item = payload.get("Item")
        if not item:
            return None

        price_data = item.get("CurrentPrice", {})
        try:
            current_price = float(price_data.get("Value", offer.price))
        except (TypeError, ValueError):
            current_price = offer.price

        pictures = item.get("PictureURL")
        extra_images: list[str] = []
        if isinstance(pictures, list):
            extra_images = [pic for pic in pictures if isinstance(pic, str)]
        elif isinstance(pictures, str):
            extra_images = [pictures]

        return ProductOfferData(
            offer_id=offer.offer_id,
            query=offer.query,
            provider=offer.provider,
            provider_label=offer.provider_label,
            external_id=offer.external_id,
            title=item.get("Title") or offer.title,
            description=offer.description,
            image_url=item.get("GalleryURL") or offer.image_url,
            extra_images=extra_images,
            price=round(current_price, 2),
            currency=price_data.get("CurrencyID", offer.currency),
            product_url=item.get("ViewItemURLForNaturalSearch") or offer.product_url,
            fetched_at=datetime.now(timezone.utc),
        )
