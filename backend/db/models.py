from __future__ import annotations
from datetime import datetime, date, time
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean, DateTime, Date, Time,
    ForeignKey, Numeric, Enum as SAEnum, JSON, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from backend.db.database import Base
import enum

class TenantStatus(str, enum.Enum): active="active"; suspended="suspended"; expired="expired"; trial="trial"
class BookingStatus(str, enum.Enum): pending="pending"; confirmed="confirmed"; cancelled="cancelled"; completed="completed"; no_show="no_show"
class PaymentStatus(str, enum.Enum): pending="pending"; paid="paid"; refunded="refunded"; failed="failed"
class UserRole(str, enum.Enum): superadmin="superadmin"; tenant_admin="tenant_admin"; staff="staff"; customer="customer"
class TicketStatus(str, enum.Enum): open="open"; in_progress="in_progress"; resolved="resolved"; closed="closed"
class BlacklistType(str, enum.Enum): full="full"; booking_limit="booking_limit"; approval_required="approval_required"

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    bot_token = Column(String(200), unique=True, nullable=False)
    owner_tg_id = Column(BigInteger, nullable=False)
    status = Column(SAEnum(TenantStatus), default=TenantStatus.trial, nullable=False)
    subscription_plan = Column(String(50), default="trial")
    subscription_expires_at = Column(DateTime, nullable=True)
    welcome_message = Column(Text, default="به سیستم نوبت‌دهی خوش آمدید!")
    logo_file_id = Column(String(200), nullable=True)
    contact_info = Column(Text, nullable=True)
    custom_policies = Column(Text, nullable=True)
    timezone = Column(String(50), default="Asia/Tehran")
    language = Column(String(10), default="fa")
    api_key = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    categories = relationship("ServiceCategory", back_populates="tenant", cascade="all, delete-orphan")
    staff_members = relationship("StaffMember", back_populates="tenant", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="tenant", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="tenant", cascade="all, delete-orphan")
    discount_codes = relationship("DiscountCode", back_populates="tenant", cascade="all, delete-orphan")
    tickets = relationship("SupportTicket", back_populates="tenant", cascade="all, delete-orphan")
    working_hours = relationship("WorkingHour", back_populates="tenant", cascade="all, delete-orphan")
    holidays = relationship("Holiday", back_populates="tenant", cascade="all, delete-orphan")

class TenantSubscription(Base):
    __tablename__ = "tenant_subscriptions"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    plan = Column(String(50), nullable=False)
    amount = Column(Numeric(12, 0), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    created_by = Column(BigInteger, nullable=False)
    note = Column(Text, nullable=True)

class AdminUser(Base):
    __tablename__ = "admin_users"
    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(100), nullable=True)
    full_name = Column(String(200), nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.superadmin)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    tg_id = Column(BigInteger, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    secondary_phone = Column(String(20), nullable=True)
    city = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    blacklist_type = Column(SAEnum(BlacklistType), nullable=True)
    blacklist_reason = Column(Text, nullable=True)
    visit_count = Column(Integer, default=0)
    total_payments = Column(Numeric(14, 0), default=0)
    last_visit = Column(DateTime, nullable=True)
    membership_date = Column(DateTime, default=datetime.utcnow)
    internal_notes = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("tenant_id", "tg_id"),)
    tenant = relationship("Tenant", back_populates="customers")
    bookings = relationship("Booking", back_populates="customer")
    crm_notes = relationship("CRMNote", back_populates="customer", cascade="all, delete-orphan")

class ServiceCategory(Base):
    __tablename__ = "service_categories"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    tenant = relationship("Tenant", back_populates="categories")
    services = relationship("Service", back_populates="category", cascade="all, delete-orphan")

class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("service_categories.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=False, default=60)
    price = Column(Numeric(12, 0), default=0)
    capacity = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    requires_payment = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    category = relationship("ServiceCategory", back_populates="services")
    bookings = relationship("Booking", back_populates="service")
    schedules = relationship("ServiceSchedule", back_populates="service", cascade="all, delete-orphan")

class ServiceSchedule(Base):
    __tablename__ = "service_schedules"
    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False)
    weekday = Column(Integer, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    slot_duration = Column(Integer, default=60)
    is_active = Column(Boolean, default=True)
    service = relationship("Service", back_populates="schedules")

class StaffMember(Base):
    __tablename__ = "staff_members"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    tg_id = Column(BigInteger, nullable=False)
    full_name = Column(String(200), nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.staff)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("tenant_id", "tg_id"),)
    tenant = relationship("Tenant", back_populates="staff_members")

class WorkingHour(Base):
    __tablename__ = "working_hours"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    weekday = Column(Integer, nullable=False)
    open_time = Column(Time, nullable=False)
    close_time = Column(Time, nullable=False)
    is_open = Column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("tenant_id", "weekday"),)
    tenant = relationship("Tenant", back_populates="working_hours")

class Holiday(Base):
    __tablename__ = "holidays"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    holiday_date = Column(Date, nullable=False)
    description = Column(String(200), nullable=True)
    __table_args__ = (UniqueConstraint("tenant_id", "holiday_date"),)
    tenant = relationship("Tenant", back_populates="holidays")

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="SET NULL"), nullable=True)
    booking_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    status = Column(SAEnum(BookingStatus), default=BookingStatus.pending)
    price = Column(Numeric(12, 0), default=0)
    discount_amount = Column(Numeric(12, 0), default=0)
    final_price = Column(Numeric(12, 0), default=0)
    discount_code_id = Column(Integer, ForeignKey("discount_codes.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    reminder_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (Index("ix_booking_tenant_date", "tenant_id", "booking_date"),)
    tenant = relationship("Tenant", back_populates="bookings")
    customer = relationship("Customer", back_populates="bookings")
    service = relationship("Service", back_populates="bookings")
    payment = relationship("Payment", back_populates="booking", uselist=False)

class WaitingList(Base):
    __tablename__ = "waiting_list"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False)
    requested_date = Column(Date, nullable=False)
    notified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, unique=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(12, 0), nullable=False)
    status = Column(SAEnum(PaymentStatus), default=PaymentStatus.pending)
    method = Column(String(50), default="manual")
    reference = Column(String(200), nullable=True)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    booking = relationship("Booking", back_populates="payment")

class DiscountCode(Base):
    __tablename__ = "discount_codes"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(50), nullable=False)
    discount_percent = Column(Integer, nullable=True)
    discount_amount = Column(Numeric(12, 0), nullable=True)
    max_uses = Column(Integer, nullable=True)
    used_count = Column(Integer, default=0)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("tenant_id", "code"),)
    tenant = relationship("Tenant", back_populates="discount_codes")

class CRMNote(Base):
    __tablename__ = "crm_notes"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    note = Column(Text, nullable=False)
    created_by = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    customer = relationship("Customer", back_populates="crm_notes")

class SupportTicket(Base):
    __tablename__ = "support_tickets"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    customer_tg_id = Column(BigInteger, nullable=False)
    subject = Column(String(300), nullable=False)
    status = Column(SAEnum(TicketStatus), default=TicketStatus.open)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tenant = relationship("Tenant", back_populates="tickets")
    messages = relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan")

class TicketMessage(Base):
    __tablename__ = "ticket_messages"
    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False)
    sender_tg_id = Column(BigInteger, nullable=False)
    is_staff = Column(Boolean, default=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    ticket = relationship("SupportTicket", back_populates="messages")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True)
    actor_tg_id = Column(BigInteger, nullable=True)
    action = Column(String(100), nullable=False)
    entity = Column(String(100), nullable=True)
    entity_id = Column(Integer, nullable=True)
    detail = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (Index("ix_audit_tenant_created", "tenant_id", "created_at"),)
