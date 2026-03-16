from fastapi import FastAPI, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from controllers import auth
from database.database import get_db, init_db, seed_users
from schemas.auth import LoginRequest, RefreshTokenRequest, LogoutRequest
from contextlib import asynccontextmanager
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Auth Service...")
    init_db()
    seed_users()
    yield
    logging.info("Shutting down Auth Service...")

app = FastAPI(
    title="Auth Service",
    description="Central Authentication Service for AI Evaluation Tool",
    version="1.0.0",
    lifespan=lifespan,
)

raw_origins = os.getenv("CORS_ALLOW_ORIGINS", "")
cors_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
allow_origin_regex = None
if not cors_origins:
    cors_origins = ["*"]
    # Allow any localhost/127.0.0.1 port in dev (covers Vite/CRA port changes)
    # allow_origin_regex = r"^https?://(localhost|127\\.0\\.0\\.1)(:\\d+)?$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/login")
async def login(
    user: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """Authenticate user and return JWT tokens."""
    token_response = auth.login(db, user)
    cookie_secure = os.getenv("COOKIE_SECURE", "").lower() in {"1", "true", "yes"}
    cookie_samesite = os.getenv("COOKIE_SAMESITE", "lax")
    response.set_cookie(
        "access_token",
        token_response.access_token,
        httponly=True,
        secure=cookie_secure,
        samesite=cookie_samesite,
    )
    response.set_cookie(
        "refresh_token",
        token_response.refresh_token,
        httponly=True,
        secure=cookie_secure,
        samesite=cookie_samesite,
    )
    return token_response

@app.post("/refresh")
async def refresh_token(token_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token."""
    return auth.refresh_access_token(db, token_data)

@app.post("/logout")
async def logout(token_data: LogoutRequest, response: Response):
    """Logout user by revoking refresh token."""
    result = auth.logout(token_data)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=7500, reload=True)
