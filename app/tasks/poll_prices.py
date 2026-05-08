from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import SessionLocal
from app.models import PriceSnapshot, WatchedItem
from app.services.search_orchestrator import SearchOrchestrator
from app.services.store import upsert_offers
from app.tasks.celery_app import celery_app


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def _poll_watched_items() -> dict[str, int]:
    orchestrator = SearchOrchestrator()

    async with SessionLocal() as session:
        statement = (
            select(WatchedItem)
            .where(WatchedItem.active.is_(True))
            .options(selectinload(WatchedItem.offer))
        )
        result = await session.execute(statement)
        watches = list(result.scalars().all())

        updated_count = 0
        for watch in watches:
            if watch.offer is None:
                continue

            refreshed_offer = await orchestrator.refresh_offer(watch.offer)
            if refreshed_offer is None:
                continue

            await upsert_offers(session, [refreshed_offer], commit=False)
            session.add(
                PriceSnapshot(
                    watch_id=watch.id,
                    offer_id=refreshed_offer.offer_id,
                    provider=refreshed_offer.provider,
                    title=refreshed_offer.title,
                    price=refreshed_offer.price,
                    currency=refreshed_offer.currency,
                    product_url=refreshed_offer.product_url,
                    image_url=refreshed_offer.image_url,
                    captured_at=_utc_now(),
                )
            )
            watch.last_polled_at = _utc_now()
            updated_count += 1

        await session.commit()

    return {
        "watched_count": len(watches),
        "updated_count": updated_count,
    }


@celery_app.task(name="app.tasks.poll_prices.poll_watch_prices")
def poll_watch_prices() -> dict[str, int]:
    return asyncio.run(_poll_watched_items())
