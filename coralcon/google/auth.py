"""
Shared Google OAuth for CoralCon.

One token, two scopes:
  - gmail.readonly   -> read rejection emails (Gmail extractor)
  - spreadsheets     -> read/write the application tracker (Sheets client)

This is the part Coral genuinely cannot do: Gmail bodies and Sheets writes
require direct Google API access. Coral stays the read/JOIN layer (it queries
the synced CSV via the `sheets` file source).

Credentials are resolved in this order:
  1. A cached token file (default ~/.coralcon/google_token.json), refreshed if stale.
  2. An installed-app OAuth flow, using either:
       - GOOGLE_CLIENT_SECRETS=/path/to/client_secret.json, or
       - GOOGLE_OAUTH_CLIENT_ID + GOOGLE_OAUTH_CLIENT_SECRET env vars.

The Google libraries are imported lazily so that importing this module on a
machine without them (or in sample mode) never fails.
"""

from __future__ import annotations

import contextvars
import json
import os
from pathlib import Path

# Gmail read + Sheets read/write. Keep in sync with both clients.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
]

_INSTALL_HINT = (
    "Google API libraries are required for Gmail/Sheets. Install them with:\n"
    "    pip install google-auth google-auth-oauthlib google-api-python-client"
)


def token_path() -> Path:
    """Where the shared Google OAuth token is cached (CLI + web use the same file)."""
    raw = os.getenv("GOOGLE_TOKEN_PATH")
    if raw:
        return Path(raw).expanduser()
    return Path.home() / ".coralcon" / "google_token.json"


# --- Serverless / per-request token override -------------------------------
# On stateless hosts (Vercel) the filesystem is ephemeral, so the token can't be
# cached to disk between requests. The web layer instead carries the token in a
# secure cookie and injects it here per request via this contextvar. The Gmail
# and Sheets clients keep calling get_credentials() unchanged.
_token_override: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "coralcon_google_token", default=None
)


def set_token_override(token_json: str | None) -> None:
    """Install (or clear) the per-request token JSON the web layer loaded from a cookie."""
    _token_override.set(token_json or None)


def current_token_cookie() -> str | None:
    """Return the minimal token JSON to persist back into the cookie, if any."""
    return _token_override.get()


def _cookie_json(creds) -> str:
    """Serialize only what's needed to rebuild + refresh creds (no client secret)."""
    expiry = getattr(creds, "expiry", None)
    return json.dumps(
        {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "scopes": list(getattr(creds, "scopes", None) or SCOPES),
            "expiry": expiry.isoformat() if expiry else None,
        }
    )


def _creds_from_override():
    """Build Credentials from the per-request override cookie, refreshing if stale.

    Client id/secret/token_uri are injected from env so they never live in the
    cookie. Returns valid Credentials or None.
    """
    raw = _token_override.get()
    if not raw:
        return None
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
    except ImportError:
        return None
    try:
        info = json.loads(raw)
    except (TypeError, ValueError):
        return None
    info = {
        "token": info.get("token"),
        "refresh_token": info.get("refresh_token"),
        "client_id": os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
        "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": info.get("scopes") or SCOPES,
    }
    try:
        creds = Credentials.from_authorized_user_info(info, SCOPES)
    except Exception:
        return None
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            save_credentials(creds)  # refreshes the override so the cookie updates
            return creds
        except Exception:
            return None
    return creds if (creds and creds.valid) else None


# Backwards-compatible private alias.
_token_path = token_path


def client_config_from_env() -> dict | None:
    """Public accessor for env-based OAuth client config (used by the web flow)."""
    return _client_config_from_env()


def has_credentials() -> bool:
    """True if a usable (valid or refreshable) token is already cached.

    Never triggers an interactive flow — safe to call on a headless server.
    """
    # Serverless / web: a per-request cookie token takes precedence over the file.
    if current_token_cookie() is not None:
        return _creds_from_override() is not None

    token_file = token_path()
    if not token_file.exists():
        return False
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
    except ImportError:
        return False
    try:
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
    except Exception:
        return False
    if creds and creds.valid:
        return True
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            save_credentials(creds)
            return True
        except Exception:
            return False
    return False


def save_credentials(creds) -> None:
    """Persist credentials.

    Always updates the per-request override (so the web layer can write the
    refreshed token back into its cookie). On non-serverless hosts also caches
    to the shared token file so the CLI reuses the same session.
    """
    _token_override.set(_cookie_json(creds))
    if not os.getenv("VERCEL"):
        _save(creds, token_path())


def _client_config_from_env() -> dict | None:
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
    if not (client_id and client_secret):
        return None
    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }


def get_credentials():
    """Return valid Google OAuth credentials, running the consent flow if needed."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(_INSTALL_HINT) from exc

    # Serverless / web: a per-request cookie token takes precedence over the file.
    override = _creds_from_override()
    if override is not None:
        return override

    token_file = _token_path()
    creds = None

    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _save(creds, token_file)
        return creds

    # Need a fresh consent flow.
    secrets_path = os.getenv("GOOGLE_CLIENT_SECRETS")
    if secrets_path and Path(secrets_path).expanduser().exists():
        flow = InstalledAppFlow.from_client_secrets_file(
            str(Path(secrets_path).expanduser()), SCOPES
        )
    else:
        config = _client_config_from_env()
        if not config:
            raise RuntimeError(
                "No Google OAuth credentials found. Set GOOGLE_CLIENT_SECRETS to a "
                "downloaded client_secret.json, OR set GOOGLE_OAUTH_CLIENT_ID and "
                "GOOGLE_OAUTH_CLIENT_SECRET. Create a Desktop OAuth client in Google "
                "Cloud Console with the Gmail API and Sheets API enabled."
            )
        flow = InstalledAppFlow.from_client_config(config, SCOPES)

    # Opens a browser and runs a loopback server on a random port.
    creds = flow.run_local_server(port=0)
    _save(creds, token_file)
    return creds


def _save(creds, token_file: Path) -> None:
    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_file.write_text(creds.to_json(), encoding="utf-8")


def access_token() -> str:
    """Return a bare access token string (useful for raw HTTP calls / Coral)."""
    return get_credentials().token
