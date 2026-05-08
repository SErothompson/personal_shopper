from app.providers.base import build_offer_id


def test_build_offer_id_stable_with_external_id() -> None:
    first = build_offer_id("ebay", "12345", "https://example.com/item/12345")
    second = build_offer_id("ebay", "12345", "https://example.com/item/99999")

    assert first == second


def test_build_offer_id_changes_for_different_provider() -> None:
    ebay_id = build_offer_id("ebay", "12345", "https://example.com/item/12345")
    bestbuy_id = build_offer_id("bestbuy", "12345", "https://example.com/item/12345")

    assert ebay_id != bestbuy_id
