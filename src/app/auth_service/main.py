from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from controllers import auth
from database.database import get_db, init_db, seed_users
from schemas.auth import LoginRequest, RefreshTokenRequest, LogoutRequest
from contextlib import asynccontextmanager
import logging

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/login")
async def login(user: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT tokens."""
    return auth.login(db, user)

@app.post("/refresh")
async def refresh_token(token_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token."""
    return auth.refresh_access_token(db, token_data)

@app.post("/logout")
async def logout(token_data: LogoutRequest):
    """Logout user by revoking refresh token."""
    return auth.logout(token_data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)