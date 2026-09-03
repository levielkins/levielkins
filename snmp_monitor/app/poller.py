import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .database import SessionLocal
from .models import Device, PollResult
from .snmp_client import poll_device

logger = logging.getLogger("snmp_monitor.poller")

# How often the scheduler checks which devices are due for a poll. Each
# device's own poll_interval_seconds decides how often it actually gets
# polled; this is just the granularity of that check.
TICK_SECONDS = 15


def _is_due(device: Device) -> bool:
    latest = device.latest_result
    if latest is None:
        return True
    return datetime.utcnow() - latest.timestamp >= timedelta(
        seconds=device.poll_interval_seconds
    )


async def poll_and_record(device_id: int) -> PollResult:
    """Poll one device and persist a PollResult row. Used by both the
    scheduler and the manual "poll now" button."""
    db = SessionLocal()
    try:
        device = db.get(Device, device_id)
        if device is None:
            raise ValueError(f"Device {device_id} not found")

        outcome = await poll_device(
            ip_address=device.ip_address,
            port=device.port,
            community=device.community,
            snmp_version=device.snmp_version,
        )

        record = PollResult(device_id=device.id, **outcome)
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    finally:
        db.close()


async def poll_due_devices() -> None:
    db = SessionLocal()
    try:
        devices = db.query(Device).filter(Device.enabled.is_(True)).all()
        due_ids = [d.id for d in devices if _is_due(d)]
    finally:
        db.close()

    for device_id in due_ids:
        try:
            await poll_and_record(device_id)
        except Exception:
            logger.exception("Failed to poll device %s", device_id)


def start_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        poll_due_devices,
        "interval",
        seconds=TICK_SECONDS,
        id="poll_due_devices",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    return scheduler
