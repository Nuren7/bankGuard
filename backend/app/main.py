from contextlib import asynccontextmanager
from decimal import Decimal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import Account
from app.routers import accounts, payments, webhooks


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.query(Account).count() == 0:
            db.add_all(
                [
                    Account(account_number="BG-1000001", balance=Decimal("100000.00"), currency="SEK"),
                    Account(account_number="BG-1000002", balance=Decimal("25000.00"), currency="SEK"),
                ]
            )
            db.commit()
    yield


app = FastAPI(title="BankGuard API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(accounts.router)
app.include_router(payments.router)
app.include_router(webhooks.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}