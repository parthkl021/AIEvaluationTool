from fastapi import FastAPI, Depends, Response, Request
from fastapi.responses import HTMLResponse, RedirectResponse
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

@app.get("/web/login", response_class=HTMLResponse)
async def web_login(return_url: str = "http://localhost:8000/dashboard"):
    html = """
    <!DOCTYPE html>
    <html lang='en'>
    <head>
      <meta charset='UTF-8' />
      <meta name='viewport' content='width=device-width, initial-scale=1.0' />
      <title>Central Login</title>
      <style>
        body {{ font-family: Arial, sans-serif; background:#f5f7ff; display:flex; justify-content:center; align-items:center; min-height:100vh; margin:0; }}
        .card {{ background:white; border-radius:12px; box-shadow:0 10px 25px rgba(0,0,0,0.08); width:min(95%,420px); padding:24px; }}
        input{{ width:100%; padding:10px; margin:0.33rem 0; border:1px solid #ced4da; border-radius:6px; }}
        button{{ width:100%; padding:10px; margin-top:10px; border:none; border-radius:6px; background:#4338ca; color:white; font-size:1rem; }}
      </style>
    </head>
    <body>
    <div class='card'>
      <h2>Central Login</h2>
      <p>Use your shared credentials across applications.</p>
      <form id='login-form'>
        <input id='user_name' name='user_name' placeholder='Username' required />
        <input id='password' name='password' placeholder='Password' type='password' required />
        <button type='submit'>Sign in</button>
      </form>
      <div id='error' style='color:#c53030;margin-top:12px; font-size:.9rem;'></div>
    </div>
    <script>
      const q = new URLSearchParams(window.location.search);
      const returnUrl = q.get('return_url') || 'http://localhost:8000/dashboard';
      document.getElementById('login-form').onsubmit = async (e) => {
        e.preventDefault();
        const user_name = document.getElementById('user_name').value;
        const password = document.getElementById('password').value;
        const res = await fetch('/login', {
          method:'POST',
          headers:{'Content-Type':'application/json'},
          body: JSON.stringify({ user_name, password })
        });
        const data = await res.json();
        if (!res.ok) {
          document.getElementById('error').innerText = data.detail || 'Login failed';
          return;
        }
        const url = new URL(returnUrl, window.location.origin);
        const fragment = new URLSearchParams({
          access_token: data.access_token,
          refresh_token: data.refresh_token,
          user_name: data.user_name,
          role: data.role,
        }).toString();
        window.location.href = `${url.toString()}#${fragment}`;
      };
    </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
@app.get("/web/logout")
async def web_logout(return_url: str = "http://localhost:8000"):
    response = RedirectResponse(url=return_url)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=7500, reload=True)
