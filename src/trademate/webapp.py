"""Password protected web application and PWA entry point for TradeMate."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
from pathlib import Path
import re
import secrets
import sqlite3
import time
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field
from dotenv import load_dotenv
import httpx

from trademate.bot import evaluate_snapshot, format_analysis, format_market_snapshot, strategy_asset_class
from trademate.market_data import BinanceSpotProvider, MarketDataError, MetaTrader5DemoProvider
from trademate.risk import RiskCalculationError, calculate_position_risk, parse_decimal
from trademate.strategy import DecisionStatus
from trademate.learning import LESSONS, TIER_NAMES


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
load_dotenv()
DB_PATH = Path(os.getenv("TRADEMATE_DB_PATH", "trademate.sqlite3")).resolve()
DATABASE_URL = os.getenv("TRADEMATE_DATABASE_URL", os.getenv("DATABASE_URL", "")).strip()
NEON_AUTH_BASE_URL = os.getenv("NEON_AUTH_BASE_URL", "").strip().rstrip("/")
NEON_AUTH_ENABLED = bool(NEON_AUTH_BASE_URL)
SESSION_DAYS = 14
HASH_N = 2**14
_attempts: dict[str, list[float]] = {}


class PostgresConnection:
    """Small DB-API bridge for the parameter style shared with SQLite."""

    def __init__(self, connection) -> None:
        self._connection = connection

    def __enter__(self):
        self._connection.__enter__()
        return self

    def __exit__(self, *args):
        return self._connection.__exit__(*args)

    def execute(self, statement: str, parameters=()):
        return self._connection.execute(statement.replace("?", "%s"), parameters)


def db():
    if DATABASE_URL:
        import psycopg
        from psycopg.rows import dict_row

        return PostgresConnection(psycopg.connect(DATABASE_URL, row_factory=dict_row))
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def hash_password(password: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
    salt = salt or secrets.token_bytes(16)
    return salt, hashlib.scrypt(password.encode("utf-8"), salt=salt, n=HASH_N, r=8, p=1)


def verify_password(password: str, salt: bytes, expected: bytes) -> bool:
    _, actual = hash_password(password, salt)
    return hmac.compare_digest(actual, expected)


def is_integrity_error(exc: Exception) -> bool:
    if isinstance(exc, sqlite3.IntegrityError):
        return True
    if DATABASE_URL:
        import psycopg

        return isinstance(exc, psycopg.IntegrityError)
    return False


def initialize_database() -> None:
    if not os.getenv("TRADEMATE_ADMIN_EMAIL", "").strip() or len(os.getenv("TRADEMATE_ADMIN_PASSWORD", "")) < 12:
        raise RuntimeError("Set TRADEMATE_ADMIN_EMAIL and a TRADEMATE_ADMIN_PASSWORD of at least 12 characters before starting the PWA.")
    with db() as connection:
        if DATABASE_URL:
            schema = """
            CREATE TABLE IF NOT EXISTS users (
                id BIGSERIAL PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                salt BYTEA,
                password_hash BYTEA,
                role TEXT NOT NULL DEFAULT 'member',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS invites (
                code_hash TEXT PRIMARY KEY,
                created_by INTEGER NOT NULL REFERENCES users(id),
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used_at TEXT
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                expires_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS lesson_progress (
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                lesson_id TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                PRIMARY KEY (user_id, lesson_id)
            );
            """
            for statement in schema.split(";"):
                if statement.strip():
                    connection.execute(statement)
        else:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    salt BLOB,
                    password_hash BLOB,
                    role TEXT NOT NULL DEFAULT 'member',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS invites (
                    code_hash TEXT PRIMARY KEY,
                    created_by INTEGER NOT NULL REFERENCES users(id),
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    used_at TEXT
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    token_hash TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    expires_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS lesson_progress (
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    lesson_id TEXT NOT NULL,
                    completed_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, lesson_id)
                );
            """)
        owner_email = os.getenv("TRADEMATE_ADMIN_EMAIL", "").strip().lower()
        owner_password = os.getenv("TRADEMATE_ADMIN_PASSWORD", "")
        if owner_email and owner_password and not connection.execute(
            "SELECT 1 FROM users WHERE email = ?", (owner_email,)
        ).fetchone():
            if NEON_AUTH_ENABLED and DATABASE_URL:
                salt, digest = None, None
            else:
                # SQLite may already have the old NOT NULL auth columns. This
                # random value is not the user's password and is never used by
                # Managed Auth.
                salt, digest = hash_password(secrets.token_urlsafe(48))
            connection.execute(
                "INSERT INTO users(email, salt, password_hash, role, created_at) VALUES (?, ?, ?, 'admin', ?)",
                (owner_email, salt, digest, datetime.now(timezone.utc).isoformat()),
            )
    if NEON_AUTH_ENABLED:
        ensure_managed_owner(owner_email, owner_password)


def ensure_managed_owner(email: str, password: str) -> None:
    """Create the configured owner in Neon Auth, or verify its existing password."""
    if not email or not password:
        return
    origin = os.getenv("TRADEMATE_PUBLIC_ORIGIN", "https://trademate-ai.netlify.app")
    headers = {"Origin": origin, "Referer": f"{origin}/"}
    try:
        created = httpx.post(
            f"{NEON_AUTH_BASE_URL}/sign-up/email",
            json={"name": email.split("@", 1)[0], "email": email, "password": password},
            headers=headers,
            timeout=20,
        )
        authenticated = created
        if created.status_code >= 400:
            authenticated = httpx.post(
                f"{NEON_AUTH_BASE_URL}/sign-in/email",
                json={"email": email, "password": password},
                headers=headers,
                timeout=20,
            )
        if authenticated.status_code >= 400:
            raise RuntimeError("Neon Auth could not create or verify the configured owner account.")
        httpx.post(
            f"{NEON_AUTH_BASE_URL}/sign-out",
            json={},
            cookies=authenticated.cookies,
            headers=headers,
            timeout=15,
        )
    except httpx.HTTPError as exc:
        raise RuntimeError("Neon Auth is unreachable; the TradeMate API cannot start safely.") from exc


def current_user(request: Request) -> Any:
    if NEON_AUTH_ENABLED:
        cookie = request.headers.get("cookie", "")
        try:
            session = httpx.get(
                f"{NEON_AUTH_BASE_URL}/get-session",
                headers={"cookie": cookie, "origin": str(request.base_url).rstrip("/")},
                timeout=15,
            )
        except httpx.HTTPError:
            raise HTTPException(503, "Authentication service is temporarily unavailable.") from None
        auth_session = session.json() if session.status_code == 200 else None
        email = (auth_session or {}).get("user", {}).get("email", "").strip().lower()
        if not email:
            raise HTTPException(401, "Please sign in to continue.")
        with db() as connection:
            row = connection.execute(
                "SELECT id, email, role FROM users WHERE email = ?", (email,)
            ).fetchone()
        if row is None:
            raise HTTPException(403, "This account has not been invited to TradeMate.")
        return row

    token = request.cookies.get("trademate_session", "")
    if not token:
        raise HTTPException(401, "Please sign in to continue.")
    digest = hashlib.sha256(token.encode()).hexdigest()
    with db() as connection:
        row = connection.execute(
            "SELECT users.id, users.email, users.role FROM sessions "
            "JOIN users ON users.id = sessions.user_id WHERE sessions.token_hash = ? AND sessions.expires_at > ?",
            (digest, datetime.now(timezone.utc).isoformat()),
        ).fetchone()
    if row is None:
        raise HTTPException(401, "Your session expired. Please sign in again.")
    return row


def owner(user: Any = Depends(current_user)) -> Any:
    if user["role"] != "admin":
        raise HTTPException(403, "Only the app owner can invite people.")
    return user


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class Signup(Credentials):
    invite_code: str = Field(min_length=16, max_length=100)


class SymbolRequest(BaseModel):
    symbol: str = Field(min_length=3, max_length=24, pattern=r"^[A-Za-z0-9._/-]+$")


class RiskPlanRequest(BaseModel):
    symbol: str = Field(min_length=3, max_length=24, pattern=r"^[A-Za-z0-9._/-]+$")
    direction: str = Field(pattern=r"^(long|short)$")
    entry: str = Field(min_length=1, max_length=30)
    stop: str = Field(min_length=1, max_length=30)
    equity: str = Field(min_length=1, max_length=30)
    equity_currency: str = Field(min_length=3, max_length=8, pattern=r"^[A-Za-z]{3,8}$")
    risk_percent: str = Field(min_length=1, max_length=8)
    target: str | None = Field(default=None, max_length=30)


class LessonAnswer(BaseModel):
    answer_index: int = Field(ge=0, le=2)


class ScanRequest(BaseModel):
    symbols: list[str] = Field(min_length=1, max_length=8)


def login_throttle(request: Request) -> None:
    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    recent = [stamp for stamp in _attempts.get(client, []) if now - stamp < 900]
    if len(recent) >= 10:
        raise HTTPException(429, "Too many attempts. Please wait 15 minutes and try again.")
    recent.append(now)
    _attempts[client] = recent


def managed_auth_post(path: str, payload: dict[str, Any], request: Request) -> httpx.Response:
    if not NEON_AUTH_ENABLED:
        raise HTTPException(503, "Neon Auth is not configured on this API.")
    headers = {}
    origin = request.headers.get("origin")
    if origin:
        origin = normalized_auth_origin(origin)
        headers["origin"] = origin
        headers["referer"] = f"{origin}/"
    agent = request.headers.get("user-agent")
    if agent:
        headers["user-agent"] = agent
    try:
        return httpx.post(
            f"{NEON_AUTH_BASE_URL}/{path.lstrip('/')}",
            json=payload,
            headers=headers,
            timeout=20,
        )
    except httpx.HTTPError:
        raise HTTPException(503, "Authentication service is temporarily unavailable.") from None


def normalized_auth_origin(origin: str) -> str:
    parsed = urlsplit(origin)
    if parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "::1"}:
        netloc = "localhost" + (f":{parsed.port}" if parsed.port else "")
        return urlunsplit((parsed.scheme, netloc, "", "", ""))
    return urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))


def copy_auth_cookies(auth_response: httpx.Response, response: Response, request: Request) -> None:
    for value in auth_response.headers.get_list("set-cookie"):
        # The browser talks to Netlify / this API through a same-origin proxy.
        # A Neon-host Domain attribute would make the browser reject the cookie;
        # removing Domain makes it host-only on the public app origin.
        host_cookie = re.sub(r";\s*Domain=[^;]+", "", value, flags=re.IGNORECASE)
        if request.url.scheme != "https" and request.url.hostname in {"localhost", "127.0.0.1", "::1"}:
            host_cookie = re.sub(r";\s*Secure", "", host_cookie, flags=re.IGNORECASE)
        response.raw_headers.append((b"set-cookie", host_cookie.encode("latin-1")))


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="TradeMate AI", docs_url=None, redoc_url=None, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/manifest.webmanifest")
def manifest() -> FileResponse:
    return FileResponse(STATIC_DIR / "manifest.webmanifest", media_type="application/manifest+json")


@app.get("/service-worker.js")
def service_worker() -> FileResponse:
    return FileResponse(STATIC_DIR / "service-worker.js", media_type="application/javascript", headers={"Service-Worker-Allowed": "/"})


@app.get("/api/auth/status")
def auth_status():
    with db() as connection:
        owner_exists = connection.execute("SELECT 1 FROM users WHERE role='admin' LIMIT 1").fetchone() is not None
    return {"owner_configured": owner_exists}


@app.post("/api/auth/login")
def login(payload: Credentials, request: Request, response: Response, _: None = Depends(login_throttle)):
    if NEON_AUTH_ENABLED:
        auth_response = managed_auth_post(
            "sign-in/email",
            {"email": payload.email.strip().lower(), "password": payload.password},
            request,
        )
        if auth_response.status_code >= 400:
            raise HTTPException(401, "Email or password is incorrect.")
        auth_data = auth_response.json()
        email = auth_data.get("user", {}).get("email", payload.email).strip().lower()
        with db() as connection:
            user = connection.execute(
                "SELECT email, role FROM users WHERE email = ?", (email,)
            ).fetchone()
        if user is None:
            raise HTTPException(403, "This account has not been invited to TradeMate.")
        copy_auth_cookies(auth_response, response, request)
        return {"email": user["email"], "role": user["role"]}

    with db() as connection:
        user = connection.execute("SELECT * FROM users WHERE email = ?", (payload.email.strip().lower(),)).fetchone()
    if user is None or not verify_password(payload.password, user["salt"], user["password_hash"]):
        raise HTTPException(401, "Email or password is incorrect.")
    token = secrets.token_urlsafe(32)
    expiry = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    with db() as connection:
        connection.execute("INSERT INTO sessions(token_hash, user_id, expires_at) VALUES (?, ?, ?)",
                           (hashlib.sha256(token.encode()).hexdigest(), user["id"], expiry.isoformat()))
    response.set_cookie("trademate_session", token, max_age=SESSION_DAYS * 86400, httponly=True,
                        secure=os.getenv("TRADEMATE_COOKIE_SECURE", "true").lower() == "true",
                        samesite="strict", path="/")
    return {"email": user["email"], "role": user["role"]}


@app.post("/api/auth/register")
def register(payload: Signup, request: Request, response: Response, _: None = Depends(login_throttle)):
    now = datetime.now(timezone.utc)
    code_hash = hashlib.sha256(payload.invite_code.strip().encode()).hexdigest()
    if NEON_AUTH_ENABLED and DATABASE_URL:
        salt, digest = None, None
    else:
        salt, digest = hash_password(
            secrets.token_urlsafe(48) if NEON_AUTH_ENABLED else payload.password
        )
    managed_response = None
    try:
        with db() as connection:
            invite = connection.execute("SELECT * FROM invites WHERE code_hash = ?", (code_hash,)).fetchone()
            if invite is None or invite["used_at"] or invite["expires_at"] <= now.isoformat():
                raise HTTPException(400, "That invite code is invalid or expired.")
            if connection.execute(
                "SELECT 1 FROM users WHERE email = ?", (payload.email.strip().lower(),)
            ).fetchone():
                raise HTTPException(409, "An account with that email already exists.")
            if NEON_AUTH_ENABLED:
                claimed = connection.execute(
                    "UPDATE invites SET used_at = ? WHERE code_hash = ? AND used_at IS NULL AND expires_at > ?",
                    (now.isoformat(), code_hash, now.isoformat()),
                )
                if claimed.rowcount != 1:
                    raise HTTPException(400, "That invite code is invalid or expired.")
                managed_response = managed_auth_post(
                    "sign-up/email",
                    {"name": payload.email.split("@", 1)[0],
                     "email": payload.email.strip().lower(), "password": payload.password},
                    request,
                )
                if managed_response.status_code >= 400:
                    if managed_response.status_code == 422 or managed_response.status_code == 409:
                        raise HTTPException(409, "An account with that email already exists.")
                    raise HTTPException(502, "Neon Auth could not create the account.")
                if DATABASE_URL:
                    salt, digest = None, None
            cursor = connection.execute(
                "INSERT INTO users(email, salt, password_hash, created_at) VALUES (?, ?, ?, ?) RETURNING id",
                (payload.email.strip().lower(), salt, digest, now.isoformat()),
            )
            user_id = cursor.fetchone()["id"]
            if not NEON_AUTH_ENABLED:
                used = connection.execute("UPDATE invites SET used_at = ? WHERE code_hash = ? AND used_at IS NULL AND expires_at > ?",
                                          (now.isoformat(), code_hash, now.isoformat()))
                if used.rowcount != 1:
                    raise HTTPException(400, "That invite code is invalid or expired.")
    except Exception as exc:
        if not is_integrity_error(exc):
            raise
        raise HTTPException(409, "An account with that email already exists.") from None
    if managed_response is not None:
        copy_auth_cookies(managed_response, response, request)
        return {"email": payload.email.strip().lower(), "role": "member"}
    token = secrets.token_urlsafe(32)
    with db() as connection:
        connection.execute("INSERT INTO sessions(token_hash, user_id, expires_at) VALUES (?, ?, ?)",
                           (hashlib.sha256(token.encode()).hexdigest(), user_id, (now + timedelta(days=SESSION_DAYS)).isoformat()))
    response.set_cookie("trademate_session", token, max_age=SESSION_DAYS * 86400, httponly=True,
                        secure=os.getenv("TRADEMATE_COOKIE_SECURE", "true").lower() == "true",
                        samesite="strict", path="/")
    return {"email": payload.email.strip().lower(), "role": "member"}


@app.post("/api/auth/logout")
def logout(request: Request, response: Response):
    if NEON_AUTH_ENABLED:
        headers = {"cookie": request.headers.get("cookie", "")}
        origin = request.headers.get("origin")
        if origin:
            headers["origin"] = normalized_auth_origin(origin)
            headers["referer"] = f"{headers['origin']}/"
        try:
            auth_response = httpx.post(
                f"{NEON_AUTH_BASE_URL}/sign-out", json={}, headers=headers, timeout=15
            )
        except httpx.HTTPError:
            raise HTTPException(503, "Authentication service is temporarily unavailable.") from None
        copy_auth_cookies(auth_response, response, request)
        response.delete_cookie("trademate_session", path="/")
        return {"ok": auth_response.status_code < 400}

    token = request.cookies.get("trademate_session", "")
    if token:
        with db() as connection:
            connection.execute("DELETE FROM sessions WHERE token_hash = ?", (hashlib.sha256(token.encode()).hexdigest(),))
    response.delete_cookie("trademate_session", path="/")
    return {"ok": True}


@app.get("/api/me")
def me(user: sqlite3.Row = Depends(current_user)):
    return {"email": user["email"], "role": user["role"]}


@app.post("/api/invites")
def create_invite(user: sqlite3.Row = Depends(owner)):
    code = secrets.token_urlsafe(24)
    now = datetime.now(timezone.utc)
    with db() as connection:
        connection.execute("INSERT INTO invites(code_hash, created_by, created_at, expires_at) VALUES (?, ?, ?, ?)",
                           (hashlib.sha256(code.encode()).hexdigest(), user["id"], now.isoformat(), (now + timedelta(days=7)).isoformat()))
    return {"invite_code": code, "expires_in_days": 7}


async def fetch_snapshot(symbol: str):
    try:
        source = os.getenv("TRADEMATE_MARKET_SOURCE", "binance").strip().lower()
        if source == "binance":
            async with BinanceSpotProvider() as provider:
                return await provider.fetch_snapshot(symbol)
        if source != "mt5":
            raise HTTPException(503, "TRADEMATE_MARKET_SOURCE must be binance or mt5.")
        return await MetaTrader5DemoProvider().fetch_snapshot(symbol)
    except MarketDataError as exc:
        raise HTTPException(503, str(exc)) from None


@app.post("/api/market")
async def market(payload: SymbolRequest, _: sqlite3.Row = Depends(current_user)):
    snapshot = await fetch_snapshot(payload.symbol.strip())
    return {"symbol": snapshot.symbol, "price": str(snapshot.last_price), "quote_currency": snapshot.quote_currency,
            "source": snapshot.source, "price_time": snapshot.price_at.isoformat(), "checked_at": snapshot.checked_at.isoformat(),
            "summary": format_market_snapshot(snapshot)}


@app.post("/api/analyze")
async def analyze(payload: SymbolRequest, _: sqlite3.Row = Depends(current_user)):
    asset_class = strategy_asset_class(payload.symbol)
    if asset_class is None:
        raise HTTPException(400, "Supported signals: currency pairs, gold, and BTC/USD.")
    snapshot = await fetch_snapshot(payload.symbol.strip())
    evaluation, analyzed_at = evaluate_snapshot(snapshot, asset_class)
    from datetime import timedelta
    wat = timezone(timedelta(hours=1), name="WAT")
    local_time = analyzed_at.astimezone(wat)
    summary = format_analysis(evaluation, symbol=snapshot.symbol, source=snapshot.source,
                              analyzed_at=analyzed_at, last_price=snapshot.last_price)
    return {"symbol": snapshot.symbol, "status": evaluation.status.value,
            "direction": evaluation.direction.value, "summary": summary,
            "checked_at": local_time.isoformat(),
            "checks": [{"name": check.name, "state": check.state.value, "evidence": check.evidence,
                        "blocks_setup": check.blocks_setup} for check in evaluation.checks],
            "levels": ({"entry": str(evaluation.entry), "stop": str(evaluation.stop),
                        "target_1": str(evaluation.tp1), "target_2": str(evaluation.tp2)}
                       if evaluation.status is DecisionStatus.TRADE_SETUP else None)}


@app.post("/api/risk")
async def risk_plan(payload: RiskPlanRequest, _: sqlite3.Row = Depends(current_user)):
    try:
        snapshot = await fetch_snapshot(payload.symbol.strip())
        result = calculate_position_risk(
            direction=payload.direction,
            entry=parse_decimal(payload.entry, "Entry price"),
            stop=parse_decimal(payload.stop, "Stop price"),
            equity=parse_decimal(payload.equity, "Account balance"),
            equity_currency=payload.equity_currency.strip().upper(),
            risk_percent=parse_decimal(payload.risk_percent, "Risk percentage"),
            specification=snapshot.risk_specification,
            target=parse_decimal(payload.target, "Target price") if payload.target else None,
        )
    except (MarketDataError, RiskCalculationError) as exc:
        raise HTTPException(400, str(exc)) from None
    return {"symbol": snapshot.symbol, "direction": result.direction,
            "quantity": str(result.quantity), "quantity_unit": snapshot.risk_specification.quantity_unit,
            "risk_amount": str(result.planned_risk_amount), "estimated_loss": str(result.estimated_loss),
            "actual_risk_percent": str(result.actual_risk_percent),
            "equity_currency": snapshot.risk_specification.currency,
            "risk_reward": str(result.risk_reward) if result.risk_reward is not None else None,
            "note": "Estimate only. Spread, commissions, slippage, gaps, and broker execution can change the real loss. TradeMate does not place trades."}


@app.get("/api/lessons")
def get_lessons(user: sqlite3.Row = Depends(current_user)):
    with db() as connection:
        completed = {row["lesson_id"] for row in connection.execute(
            "SELECT lesson_id FROM lesson_progress WHERE user_id = ?", (user["id"],))}
    return {"tiers": TIER_NAMES, "completed": sorted(completed),
            "lessons": [{key: lesson[key] for key in ("id", "tier", "title", "content", "question", "options")}
                        | {"completed": lesson["id"] in completed} for lesson in LESSONS]}


@app.post("/api/lessons/{lesson_id}/answer")
def answer_lesson(lesson_id: str, payload: LessonAnswer, user: sqlite3.Row = Depends(current_user)):
    lesson = next((item for item in LESSONS if item["id"] == lesson_id), None)
    if lesson is None:
        raise HTTPException(404, "Lesson not found.")
    correct = payload.answer_index == lesson["answer"]
    if correct:
        with db() as connection:
            connection.execute("INSERT INTO lesson_progress(user_id, lesson_id, completed_at) VALUES (?, ?, ?) ON CONFLICT (user_id, lesson_id) DO NOTHING",
                               (user["id"], lesson_id, datetime.now(timezone.utc).isoformat()))
    return {"correct": correct, "explanation": lesson["explanation"], "completed": correct}


@app.post("/api/scan")
async def scan(payload: ScanRequest, _: sqlite3.Row = Depends(current_user)):
    results = []
    for raw_symbol in payload.symbols:
        symbol = raw_symbol.strip()
        if not symbol or len(symbol) > 24:
            results.append({"symbol": symbol[:24], "error": "Enter a valid symbol."})
            continue
        try:
            snapshot = await fetch_snapshot(symbol)
            asset_class = strategy_asset_class(symbol)
            evaluation = evaluate_snapshot(snapshot, asset_class)[0] if asset_class else None
            results.append({"symbol": snapshot.symbol, "price": str(snapshot.last_price),
                            "status": evaluation.status.value if evaluation else "PRICE ONLY",
                            "direction": evaluation.direction.value if evaluation else None,
                            "source": snapshot.source})
        except (MarketDataError, HTTPException) as exc:
            results.append({"symbol": symbol, "error": exc.detail if isinstance(exc, HTTPException) else str(exc)})
    return {"results": results}


@app.get("/api/health")
def health():
    return {"status": "ok"}
