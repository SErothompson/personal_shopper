from collections.abc import Sequence

from app.schemas import ProductOfferData


def compute_cheapest_offer(offers: Sequence[ProductOfferData]) -> ProductOfferData | None:
    priced = [offer for offer in offers if offer.price >= 0]
    if not priced:
        return None
    return min(priced, key=lambda item: item.price)
