import os
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Header, Query, Path, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, ForeignKey, DateTime, func, Float, Text

# Database setup using environment variables (must be provided via .env)
# Expected env var: DATABASE_URL (e.g., postgresql+asyncpg://user:pass@host:5432/dbname)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Keep code resilient: use a placeholder SQLite memory db when env not set (for local CI run)
    # NOTE: For production, set DATABASE_URL in .env
    DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()

# SQLAlchemy models (minimal schema to support routes)
class UserORM(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, default="user")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BookingORM(Base):
    __tablename__ = "bookings"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    room_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    seat_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PaymentORM(Base):
    __tablename__ = "payments"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id"))
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="initiated")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class NotificationORM(Base):
    __tablename__ = "notifications"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(String)
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# PUBLIC_INTERFACE
async def get_db() -> AsyncSession:
    """Dependency that yields an AsyncSession for DB operations."""
    async with async_session() as session:
        yield session


# Pydantic models for API contracts
class ErrorModel(BaseModel):
    code: str
    message: str
    details: Optional[str] = None


class User(BaseModel):
    id: str = Field(..., description="Unique identifier for the user")
    email: EmailStr
    name: str
    role: str = Field(default="user", description="Role of the user: user or admin")
    created_at: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    accessToken: str
    refreshToken: str
    user: User


class Booking(BaseModel):
    id: str
    user_id: str
    room_id: Optional[str] = None
    seat_id: Optional[str] = None
    status: str = Field(default="pending")
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PaginatedResult(BaseModel):
    page: int
    pageSize: int
    total: int
    items: List[dict]


class Payment(BaseModel):
    id: str
    booking_id: str
    amount: float
    currency: str
    status: str = Field(default="initiated")
    created_at: Optional[str] = None


class Notification(BaseModel):
    id: str
    user_id: str
    type: str
    message: str
    created_at: Optional[str] = None


class AdminAction(BaseModel):
    id: str
    adminId: str
    action: str
    targetId: str
    timestamp: str


openapi_tags = [
    {"name": "Health", "description": "Service health and info"},
    {"name": "Users", "description": "User registration, login, and management"},
    {"name": "Bookings", "description": "Booking operations"},
    {"name": "Payments", "description": "Payment operations"},
    {"name": "Notifications", "description": "User notifications"},
    {"name": "Admin", "description": "Administrative operations"},
]

app = FastAPI(
    title="Ticket Booking API",
    description="RESTful API for ticket booking application, supporting user management, booking workflows, payments, and admin operations.",
    version="1.0.0",
    openapi_tags=openapi_tags,
)

# CORS setup honoring common frontend envs; allow all in dev by default
frontend_url = os.getenv("REACT_APP_FRONTEND_URL", "*")
backend_url = os.getenv("REACT_APP_BACKEND_URL", "*")
allow_origins = [o for o in [frontend_url, backend_url] if o]
if "*" in allow_origins:
    allow_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PUBLIC_INTERFACE
@app.on_event("startup")
async def on_startup():
    """Initialize database schema on startup (for demo scaffolding)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# PUBLIC_INTERFACE
@app.get("/", tags=["Health"], summary="Health Check")
def health_check():
    """Basic health check endpoint for uptime verification."""
    return {"status": "ok"}

# Users
# PUBLIC_INTERFACE
@app.post("/users", tags=["Users"], status_code=status.HTTP_201_CREATED, summary="Create user")
async def create_user(user: User, db: AsyncSession = Depends(get_db)):
    """Create a new user."""
    orm = UserORM(id=user.id, email=user.email, name=user.name, role=user.role)
    db.add(orm)
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    await db.refresh(orm)
    return {
        "id": orm.id,
        "email": orm.email,
        "name": orm.name,
        "role": orm.role,
        "created_at": orm.created_at.isoformat() if orm.created_at else None,
    }

# PUBLIC_INTERFACE
@app.get("/users", tags=["Users"], summary="List users")
async def list_users(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List users with pagination."""
    from sqlalchemy import select
    result = await db.execute(select(UserORM).limit(limit).offset(offset))
    rows = result.scalars().all()
    return [
        {
            "id": r.id,
            "email": r.email,
            "name": r.name,
            "role": r.role,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]

# PUBLIC_INTERFACE
@app.get("/users/{id}", tags=["Users"], summary="Get user by ID")
async def get_user(id: str = Path(...), db: AsyncSession = Depends(get_db)):
    """Get a user by ID."""
    user = await db.get(UserORM, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }

# PUBLIC_INTERFACE
@app.put("/users/{id}", tags=["Users"], summary="Update user")
async def update_user(id: str, user: User, db: AsyncSession = Depends(get_db)):
    """Update user details."""
    existing = await db.get(UserORM, id)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    existing.email = user.email
    existing.name = user.name
    existing.role = user.role
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    await db.refresh(existing)
    return {
        "id": existing.id,
        "email": existing.email,
        "name": existing.name,
        "role": existing.role,
        "created_at": existing.created_at.isoformat() if existing.created_at else None,
    }

# PUBLIC_INTERFACE
@app.delete("/users/{id}", tags=["Users"], status_code=status.HTTP_204_NO_CONTENT, summary="Delete user")
async def delete_user(id: str, db: AsyncSession = Depends(get_db)):
    """Delete user by ID."""
    existing = await db.get(UserORM, id)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(existing)
    await db.commit()
    return

# PUBLIC_INTERFACE
@app.post("/users/login", tags=["Users"], summary="User login")
async def login_user(payload: LoginRequest):
    """Dummy login endpoint returning mock tokens for scaffolding."""
    # In production: validate credentials, issue JWT tokens
    dummy_user = User(id="u-" + payload.email, email=payload.email, name="User", role="user")
    return {
        "accessToken": "mock-access-token",
        "refreshToken": "mock-refresh-token",
        "user": dummy_user.model_dump(),
    }

# Bookings
# PUBLIC_INTERFACE
@app.get("/bookings", tags=["Bookings"], summary="List bookings")
async def list_bookings(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
):
    """List bookings with pagination."""
    from sqlalchemy import select
    stmt = select(BookingORM)
    if status_filter:
        stmt = stmt.where(BookingORM.status == status_filter)
    result = await db.execute(stmt.limit(limit).offset(offset))
    rows = result.scalars().all()
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "room_id": r.room_id,
            "seat_id": r.seat_id,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in rows
    ]

# PUBLIC_INTERFACE
@app.post("/bookings", tags=["Bookings"], status_code=status.HTTP_201_CREATED, summary="Create booking")
async def create_booking(booking: Booking, db: AsyncSession = Depends(get_db), idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key")):
    """Create a booking. Idempotency-Key is accepted but not persisted in this scaffold."""
    orm = BookingORM(
        id=booking.id,
        user_id=booking.user_id,
        room_id=booking.room_id,
        seat_id=booking.seat_id,
        status=booking.status or "pending",
    )
    db.add(orm)
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    await db.refresh(orm)
    return {
        "id": orm.id,
        "user_id": orm.user_id,
        "room_id": orm.room_id,
        "seat_id": orm.seat_id,
        "status": orm.status,
        "created_at": orm.created_at.isoformat() if orm.created_at else None,
        "updated_at": orm.updated_at.isoformat() if orm.updated_at else None,
    }

# PUBLIC_INTERFACE
@app.get("/bookings/{id}", tags=["Bookings"], summary="Get booking by ID")
async def get_booking(id: str, db: AsyncSession = Depends(get_db)):
    """Get a booking by ID."""
    b = await db.get(BookingORM, id)
    if not b:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {
        "id": b.id,
        "user_id": b.user_id,
        "room_id": b.room_id,
        "seat_id": b.seat_id,
        "status": b.status,
        "created_at": b.created_at.isoformat() if b.created_at else None,
        "updated_at": b.updated_at.isoformat() if b.updated_at else None,
    }

# PUBLIC_INTERFACE
@app.put("/bookings/{id}", tags=["Bookings"], summary="Update booking")
async def update_booking(id: str, booking: Booking, db: AsyncSession = Depends(get_db)):
    """Update an existing booking."""
    existing = await db.get(BookingORM, id)
    if not existing:
        raise HTTPException(status_code=404, detail="Booking not found")
    existing.user_id = booking.user_id
    existing.room_id = booking.room_id
    existing.seat_id = booking.seat_id
    existing.status = booking.status
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    await db.refresh(existing)
    return {
        "id": existing.id,
        "user_id": existing.user_id,
        "room_id": existing.room_id,
        "seat_id": existing.seat_id,
        "status": existing.status,
        "created_at": existing.created_at.isoformat() if existing.created_at else None,
        "updated_at": existing.updated_at.isoformat() if existing.updated_at else None,
    }

# PUBLIC_INTERFACE
@app.delete("/bookings/{id}", tags=["Bookings"], status_code=status.HTTP_204_NO_CONTENT, summary="Cancel booking")
async def cancel_booking(id: str, db: AsyncSession = Depends(get_db)):
    """Cancel (delete) a booking by ID."""
    existing = await db.get(BookingORM, id)
    if not existing:
        raise HTTPException(status_code=404, detail="Booking not found")
    await db.delete(existing)
    await db.commit()
    return

# Payments
# PUBLIC_INTERFACE
@app.post("/payments", tags=["Payments"], status_code=status.HTTP_201_CREATED, summary="Initiate payment")
async def initiate_payment(payment: Payment, db: AsyncSession = Depends(get_db)):
    """Initiate a payment for a booking."""
    orm = PaymentORM(
        id=payment.id,
        booking_id=payment.booking_id,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status or "initiated",
    )
    db.add(orm)
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    await db.refresh(orm)
    return {
        "id": orm.id,
        "booking_id": orm.booking_id,
        "amount": orm.amount,
        "currency": orm.currency,
        "status": orm.status,
        "created_at": orm.created_at.isoformat() if orm.created_at else None,
    }

# PUBLIC_INTERFACE
@app.get("/payments/{id}", tags=["Payments"], summary="Get payment status")
async def get_payment(id: str, db: AsyncSession = Depends(get_db)):
    """Get payment by ID."""
    p = await db.get(PaymentORM, id)
    if not p:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {
        "id": p.id,
        "booking_id": p.booking_id,
        "amount": p.amount,
        "currency": p.currency,
        "status": p.status,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }

# Notifications
# PUBLIC_INTERFACE
@app.get("/notifications", tags=["Notifications"], summary="List notifications for user")
async def list_notifications(userId: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    """List notifications (optionally by userId)."""
    from sqlalchemy import select
    stmt = select(NotificationORM)
    if userId:
        stmt = stmt.where(NotificationORM.user_id == userId)
    res = await db.execute(stmt)
    rows = res.scalars().all()
    return [
        {
            "id": n.id,
            "user_id": n.user_id,
            "type": n.type,
            "message": n.message,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in rows
    ]

# Admin
# PUBLIC_INTERFACE
@app.post("/admin/actions", tags=["Admin"], status_code=status.HTTP_201_CREATED, summary="Record an admin action")
async def record_admin_action(action: AdminAction):
    """Record an admin action. In this scaffold, we just echo the input."""
    return action


# Run settings
# This container should listen on port 3001. A launcher like `uvicorn src.api.main:app --host 0.0.0.0 --port 3001`
# will honor this. For reference, we expose app only (no direct run guard to match common container runners).
