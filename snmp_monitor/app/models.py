from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


def utcnow():
    # Naive UTC on purpose: SQLite has no timezone-aware datetime type, so
    # storing tz-aware values and reading them back naive invites bugs when
    # comparing "now" against a stored timestamp. Every datetime in this app
    # is UTC, kept naive, end to end.
    return datetime.utcnow()


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=utcnow)

    devices = relationship(
        "Device", back_populates="customer", cascade="all, delete-orphan"
    )


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    name = Column(String, nullable=False)
    ip_address = Column(String, nullable=False)
    port = Column(Integer, default=161)
    snmp_version = Column(String, default="2c")  # "1" or "2c"
    community = Column(String, default="public")
    poll_interval_seconds = Column(Integer, default=300)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

    customer = relationship("Customer", back_populates="devices")
    poll_results = relationship(
        "PollResult",
        back_populates="device",
        cascade="all, delete-orphan",
        order_by="desc(PollResult.timestamp)",
    )

    @property
    def latest_result(self):
        return self.poll_results[0] if self.poll_results else None


class PollResult(Base):
    __tablename__ = "poll_results"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    timestamp = Column(DateTime, default=utcnow, index=True)
    is_up = Column(Boolean, nullable=False)
    response_time_ms = Column(Float, nullable=True)
    sys_descr = Column(String, nullable=True)
    sys_name = Column(String, nullable=True)
    sys_uptime = Column(String, nullable=True)
    sys_contact = Column(String, nullable=True)
    sys_location = Column(String, nullable=True)
    error_message = Column(String, nullable=True)

    device = relationship("Device", back_populates="poll_results")
