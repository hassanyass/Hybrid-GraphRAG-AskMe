"""
Auth API routes.

Public endpoints for user registration and login.

- /register  Creates a new account via the Supabase admin API (auto-confirms
             the email so no confirmation email is required) then signs the
             user in and returns a live JWT session.

- /login     Signs an existing user in via the Supabase public token endpoint
             and returns a live JWT session.

NOTE: Uses direct HTTP calls to the Supabase REST API instead of the
supabase-py admin client because that SDK rejects the new 'sb_secret_*'
key format at the SDK layer even though the REST API accepts them fine.
"""

import os
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _supabase_url() -> str:
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    if not url:
        raise RuntimeError("SUPABASE_URL environment variable is not set.")
    return url


def _service_key() -> str:
    key = os.getenv("SUPABASE_SERVICE_KEY", "")
    if not key:
        raise RuntimeError("SUPABASE_SERVICE_KEY environment variable is not set.")
    return key


def _anon_key() -> str:
    key = os.getenv("SUPABASE_ANON_KEY", "")
    if not key:
        raise RuntimeError("SUPABASE_ANON_KEY environment variable is not set.")
    return key


def _admin_headers() -> dict[str, str]:
    """Headers for Supabase admin (service-role) endpoints."""
    key = _service_key()
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def _anon_headers() -> dict[str, str]:
    """Headers for Supabase public auth endpoints."""
    key = _anon_key()
    return {
        "apikey": key,
        "Content-Type": "application/json",
    }


def _extract_error(body: Any) -> str:
    """Pull the most useful error string out of a Supabase error response."""
    if isinstance(body, dict):
        return (
            body.get("msg")
            or body.get("message")
            or body.get("error_description")
            or body.get("error")
            or "Unknown error."
        )
    return str(body)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: str
    email: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/register", response_model=AuthResponse)
async def register(payload: RegisterRequest) -> AuthResponse:
    """
    Register a new user and immediately sign them in.

    Uses the Supabase admin REST API to create the account with
    email_confirm=True (no confirmation email required), then signs the
    user in via the public token endpoint and returns a live session.
    """
    email = payload.email.strip().lower()

    if not email.endswith(".com"):
        raise HTTPException(status_code=422, detail="Email must end with .com")

    base = _supabase_url()

    async with httpx.AsyncClient(timeout=20.0) as client:

        # 1. Create the user via admin API (bypasses email confirmation)
        create_resp = await client.post(
            f"{base}/auth/v1/admin/users",
            headers=_admin_headers(),
            json={
                "email": email,
                "password": payload.password,
                "email_confirm": True,
            },
        )

        if create_resp.status_code not in (200, 201):
            body = create_resp.json() if create_resp.content else {}
            raise HTTPException(status_code=400, detail=_extract_error(body))

        user_data = create_resp.json()
        user_id: str = user_data.get("id", "")

        # 2. Sign the user in to get a live JWT session
        session = await _password_sign_in(client, base, email, payload.password)

    return AuthResponse(
        access_token=session["access_token"],
        refresh_token=session["refresh_token"],
        user_id=user_id,
        email=email,
    )


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest) -> AuthResponse:
    """
    Sign an existing user in and return a live JWT session.

    Validates credentials against Supabase and returns access + refresh tokens
    that the frontend can use to restore the Supabase JS client session.
    """
    email = payload.email.strip().lower()
    base = _supabase_url()

    async with httpx.AsyncClient(timeout=20.0) as client:
        session = await _password_sign_in(client, base, email, payload.password)

    return AuthResponse(
        access_token=session["access_token"],
        refresh_token=session["refresh_token"],
        user_id=session.get("user", {}).get("id", ""),
        email=email,
    )


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------

async def _password_sign_in(
    client: httpx.AsyncClient,
    base: str,
    email: str,
    password: str,
) -> dict:
    """
    Call the Supabase public token endpoint with email+password credentials.
    Raises HTTPException on failure; returns the parsed JSON body on success.
    """
    resp = await client.post(
        f"{base}/auth/v1/token?grant_type=password",
        headers=_anon_headers(),
        json={"email": email, "password": password},
    )

    body = resp.json() if resp.content else {}

    if resp.status_code != 200:
        raise HTTPException(
            status_code=401,
            detail=_extract_error(body),
        )

    access_token = body.get("access_token", "")
    if not access_token:
        raise HTTPException(
            status_code=400,
            detail="Sign-in succeeded but no access token was returned.",
        )

    return body
