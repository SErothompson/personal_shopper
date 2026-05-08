from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PriceSnapshot, ProductOffer, WatchedItem
from app.schemas import ProductOfferData


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def upsert_offers(
    session: AsyncSession,
    offers: list[ProductOfferData],
    *,
    commit: bool = True,
) -> None:
    for offer in offers:
        existing = await session.get(ProductOffer, offer.offer_id)
        if existing is None:
            session.add(
                ProductOffer(
                    offer_id=offer.offer_id,
                    query=offer.query,
                    provider=offer.provider,
                    provider_label=offer.provider_label,
                    external_id=offer.external_id,
                    title=offer.title,
                    description=offer.description,
                    image_url=offer.image_url,
                    extra_images=offer.extra_images,
                    price=offer.price,
                    currency=offer.currency,
                    product_url=offer.product_url,
                    fetched_at=offer.fetched_at,
                )
            )
            continue

        existing.query = offer.query
        existing.provider = offer.provider
        existing.provider_label = offer.provider_label
        existing.external_id = offer.external_id
        existing.title = offer.title
        existing.description = offer.description
        existing.image_url = offer.image_url
        existing.extra_images = offer.extra_images
        existing.price = offer.price
        existing.currency = offer.currency
        existing.product_url = offer.product_url
        existing.fetched_at = offer.fetched_at

    if commit:
        await session.commit()


async def get_offer_by_id(session: AsyncSession, offer_id: str) -> ProductOffer | None:
    return await session.get(ProductOffer, offer_id)


async def get_active_watch(session: AsyncSession, offer_id: str) -> WatchedItem | None:
    statement = (
        select(WatchedItem)
        .where(WatchedItem.offer_id == offer_id)
        .where(WatchedItem.active.is_(True))
        .order_by(WatchedItem.created_at.desc())
    )
    result = await session.execute(statement)
    return result.scalars().first()


async def toggle_watch(session: AsyncSession, offer: ProductOffer) -> tuple[WatchedItem, bool]:
    watch = await get_active_watch(session, offer.offer_id)
    if watch is not None:
        watch.active = False
        await session.commit()
        return watch, False

    watch = WatchedItem(offer_id=offer.offer_id, active=True)
    session.add(watch)
    await session.flush()

    session.add(
        PriceSnapshot(
            watch_id=watch.id,
            offer_id=offer.offer_id,
            provider=offer.provider,
            title=offer.title,
            price=offer.price,
            currency=offer.currency,
            product_url=offer.product_url,
            image_url=offer.image_url,
            captured_at=_utc_now(),
        )
    )
    await session.commit()
    await session.refresh(watch)
    return watch, True
