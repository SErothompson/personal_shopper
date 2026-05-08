from app.schemas import ProductOfferData
from app.services.pricing import compute_cheapest_offer


def build_offer(offer_id: str, price: float) -> ProductOfferData:
    return ProductOfferData(
        offer_id=offer_id,
        query="headphones",
        provider="demo",
        provider_label="Demo",
        external_id=None,
        title="Offer",
        description="Offer description",
        image_url=None,
        extra_images=[],
        price=price,
        currency="USD",
        product_url="https://example.com",
    )


def test_compute_cheapest_offer_returns_lowest_price() -> None:
    offers = [build_offer("a", 29.99), build_offer("b", 19.99), build_offer("c", 24.50)]

    result = compute_cheapest_offer(offers)

    assert result is not None
    assert result.offer_id == "b"
    assert result.price == 19.99


def test_compute_cheapest_offer_with_no_offers() -> None:
    result = compute_cheapest_offer([])

    assert result is None
