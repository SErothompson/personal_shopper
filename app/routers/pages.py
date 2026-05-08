from __future__ import annotations

import json
from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import PriceSnapshot
from app.services.pricing import compute_cheapest_offer
from app.services.search_orchestrator import SearchOrchestrator
from app.services.store import get_active_watch, get_offer_by_id, toggle_watch, upsert_offers

router = APIRouter()


@router.get("/", name="home")
async def home(request: Request):
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "Personal Shopper Assistant",
            "query": "",
            "search_results": [],
            "provider_statuses": [],
            "cheapest_offer": None,
        },
    )


@router.get("/search", name="search")
async def search(
    request: Request,
    q: str = Query(min_length=2, max_length=300),
    session: AsyncSession = Depends(get_session),
):
    query = q.strip()
    orchestrator = SearchOrchestrator()
    search_response = await orchestrator.search(query)

    await upsert_offers(session, search_response.offers)
    cheapest_offer = compute_cheapest_offer(search_response.offers)

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": f"Search: {query}",
            "query": query,
            "search_results": search_response.offers,
            "provider_statuses": search_response.statuses,
            "cheapest_offer": cheapest_offer,
        },
    )


@router.get("/items/{offer_id}", name="item_detail")
async def item_detail(
    request: Request,
    offer_id: str,
    session: AsyncSession = Depends(get_session),
):
    offer = await get_offer_by_id(session, offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="Offer not found")

    watch = await get_active_watch(session, offer_id)
    snapshots: list[PriceSnapshot] = []
    if watch is not None:
        statement = (
            select(PriceSnapshot)
            .where(PriceSnapshot.watch_id == watch.id)
            .order_by(PriceSnapshot.captured_at.asc())
        )
        result = await session.execute(statement)
        snapshots = list(result.scalars().all())

    chart_points = []
    for snapshot in snapshots:
        captured_at = snapshot.captured_at
        if captured_at.tzinfo is None:
            captured_at = captured_at.replace(tzinfo=timezone.utc)
        chart_points.append(
            {
                "ts": captured_at.isoformat(),
                "price": snapshot.price,
            }
        )

    if not chart_points:
        fetched_at = offer.fetched_at
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=timezone.utc)
        chart_points.append(
            {
                "ts": fetched_at.isoformat(),
                "price": offer.price,
            }
        )

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request,
        name="item_detail.html",
        context={
            "title": offer.title,
            "offer": offer,
            "is_watching": watch is not None,
            "chart_points_json": json.dumps(chart_points),
        },
    )


@router.post("/items/{offer_id}/watch", name="toggle_watch")
async def toggle_offer_watch(
    request: Request,
    offer_id: str,
    session: AsyncSession = Depends(get_session),
):
    offer = await get_offer_by_id(session, offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="Offer not found")

    await toggle_watch(session, offer)
    return RedirectResponse(
        request.url_for("item_detail", offer_id=offer_id),
        status_code=303,
    )


@router.get("/healthz", name="healthz")
async def healthz():
    return {"ok": True}
