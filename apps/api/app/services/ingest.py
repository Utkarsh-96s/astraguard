"""Data ingestion service for persisting telemetry, TLEs, and imagery."""
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Asset, Conjunction, DisasterEvent, ImageryProduct, SpaceObject, Telemetry
from app.schemas.conjunction import ConjunctionItem
from app.schemas.disaster import DisasterEventItem, ImageryProductItem
from app.schemas.objects import SpaceObjectItem
from app.schemas.telemetry import TelemetryItem


async def ensure_asset_exists(db: AsyncSession, asset_id: str, name: str = "Mission Primary Asset") -> Asset:
    """Ensure an asset record exists in the database, creating one if missing."""
    stmt = select(Asset).where(Asset.id == asset_id)
    res = await db.execute(stmt)
    asset = res.scalar_one_or_none()
    if not asset:
        asset = Asset(
            id=asset_id,
            name=name,
            norad_id=40697,
            type="satellite",
            created_at=datetime.now(UTC),
        )
        db.add(asset)
        await db.commit()
        await db.refresh(asset)
    return asset


async def ingest_telemetry_batch(db: AsyncSession, readings: list[TelemetryItem]) -> int:
    """Bulk insert telemetry readings into the database."""
    if not readings:
        return 0

    # Ensure all target assets exist
    asset_ids = {r.asset_id for r in readings}
    for a_id in asset_ids:
        await ensure_asset_exists(db, a_id)

    db_records = [
        Telemetry(
            asset_id=r.asset_id,
            ts=r.ts,
            channel=r.channel,
            value=r.value,
            quality=r.quality,
            synthetic=r.synthetic,
        )
        for r in readings
    ]
    db.add_all(db_records)
    await db.commit()
    return len(db_records)


async def ingest_space_objects(db: AsyncSession, objects: list[SpaceObjectItem]) -> int:
    """Insert or update space objects in the catalog."""
    if not objects:
        return 0

    count = 0
    for obj in objects:
        stmt = select(SpaceObject).where(SpaceObject.norad_id == obj.norad_id)
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            existing.name = obj.name
            existing.type = obj.type
            existing.tle_line1 = obj.tle_line1
            existing.tle_line2 = obj.tle_line2
            existing.epoch = obj.epoch
            existing.updated_at = datetime.now(UTC)
        else:
            new_obj = SpaceObject(
                norad_id=obj.norad_id,
                name=obj.name,
                type=obj.type,
                tle_line1=obj.tle_line1,
                tle_line2=obj.tle_line2,
                epoch=obj.epoch,
                updated_at=datetime.now(UTC),
            )
            db.add(new_obj)
        count += 1

    await db.commit()
    return count


async def ingest_disaster_event(
    db: AsyncSession,
    product: ImageryProductItem,
    event: DisasterEventItem,
) -> tuple[str, str]:
    """Insert an imagery product and its detected disaster event."""
    # Check or insert product
    stmt_prod = select(ImageryProduct).where(ImageryProduct.id == product.id)
    res_prod = await db.execute(stmt_prod)
    existing_prod = res_prod.scalar_one_or_none()
    if not existing_prod:
        new_prod = ImageryProduct(
            id=product.id,
            source=product.source,
            bbox=product.bbox,
            acquired_at=product.acquired_at,
            cloud_pct=product.cloud_pct,
            uri=product.uri,
            created_at=datetime.now(UTC),
        )
        db.add(new_prod)

    # Insert or update disaster event
    stmt_ev = select(DisasterEvent).where(DisasterEvent.id == event.id)
    res_ev = await db.execute(stmt_ev)
    existing_ev = res_ev.scalar_one_or_none()
    if not existing_ev:
        new_ev = DisasterEvent(
            id=event.id,
            product_id=product.id,
            type=event.type,
            area_km2=event.area_km2,
            mask_uri=event.mask_uri,
            priority=event.priority,
            confidence=event.confidence,
            synthetic=event.synthetic,
            created_at=event.created_at,
        )
        db.add(new_ev)

    await db.commit()
    return product.id, event.id


async def ingest_conjunction_event(db: AsyncSession, item: ConjunctionItem) -> str:
    """Insert or update a conjunction event."""
    await ensure_asset_exists(db, item.primary_id)

    # Ensure secondary object exists in objects table
    stmt_obj = select(SpaceObject).where(SpaceObject.norad_id == item.secondary_id)
    res_obj = await db.execute(stmt_obj)
    if not res_obj.scalar_one_or_none():
        dummy_obj = SpaceObject(
            norad_id=item.secondary_id,
            name=f"DEBRIS-{item.secondary_id}",
            type="debris",
            tle_line1="1 99999U          26292.00000000  .00000000  00000-0  00000-0 0  0001",
            tle_line2="2 99999  98.0000 000.0000 0001000 000.0000 000.0000 14.3000000000001",
            epoch=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db.add(dummy_obj)

    stmt_conj = select(Conjunction).where(Conjunction.id == item.id)
    res_conj = await db.execute(stmt_conj)
    existing_conj = res_conj.scalar_one_or_none()
    if not existing_conj:
        new_conj = Conjunction(
            id=item.id,
            primary_id=item.primary_id,
            secondary_id=item.secondary_id,
            tca=item.tca,
            miss_km=item.miss_km,
            rel_vel_kms=item.rel_vel_kms,
            pc=item.pc,
            pc_method=item.pc_method,
            risk_class=item.risk_class,
            synthetic=item.synthetic,
            created_at=item.created_at,
        )
        db.add(new_conj)

    await db.commit()
    return item.id
