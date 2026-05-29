"""
Web (redirect-based) Google OAuth for CoralCon.

The CLI uses an installed-app flow (`run_local_server`) that pops a browser on
the same machine. That can't work for a deployed dashboard: there's no browser
on the server. So the web app uses the standard Authorization Code redirect:

  1. /api/google/connect builds an authorization URL and 302s the user to Google.
  2. Google redirects back to /oauth2callback?code=... on our site.
  3. We exchange the code for credentials and save them to the SHARED token path
     (the same file the CLI uses), so both halves of CoralCon stay in sync.

Google Cloud setup the user must do once:
  - Create an OAuth client of type "Web application".
  - Add the deployed callback as an Authorized redirect URI, e.g.
        https://coralcon.onrender.com/oauth2callback
    (and http://localhost:8000/oauth2callback for local testing).
  - While the app is in "testing", add the Google account as a test user.

Credentials come from the same env vars as the CLI flow:
  - GOOGLE_CLIENT_SECRETS=/path/to/client_secret.json  (web client), OR
  - GOOGLE_OAUTH_CLIENT_ID + GOOGLE_OAUTH_CLIENT_SECRET.
"""

from __future__ import annotations

import os
from pathlib import Path

from . import auth

# Where Google sends the user back. If unset we derive it from the request.
_REDIRECT_ENV = "OAUTH_REDIRECT_URI"
_CALLBACK_PATH = "/oauth2callback"

_INSTALL_HINT = (
    "Google API libraries are required for the web OAuth flow. Install them with:\n"
    "    pip install google-auth google-auth-oauthlib google-api-python-client"
)


def _web_client_config_from_env() -> dict | None:
    """Like auth._client_config_from_env, but shaped as a 'web' client.

    The redirect flow wants the config under the "web" key (not "installed").
    """
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
    if not (client_id and client_secret):
        return None
    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }


def redirect_uri(request_base_url: str | None = None) -> str:
    """Resolve the OAuth callback URL.

    Priority: OAUTH_REDIRECT_URI env var, else derived from the request's base
    URL (so it works on localhost and on the deployed host without config).
    """
    explicit = os.getenv(_REDIRECT_ENV)
    if explicit:
        return explicit
    if request_base_url:
        return request_base_url.rstrip("/") + _CALLBACK_PATH
    # Last-resort default for local dev.
    return "http://localhost:8000" + _CALLBACK_PATH


def _build_flow(redirect: str):
    try:
        from google_auth_oauthlib.flow import Flow
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(_INSTALL_HINT) from exc

    secrets_path = os.getenv("GOOGLE_CLIENT_SECRETS")
    if secrets_path and Path(secrets_path).expanduser().exists():
        flow = Flow.from_client_secrets_file(
            str(Path(secrets_path).expanduser()),
            scopes=auth.SCOPES,
            redirect_uri=redirect,
        )
    else:
        config = _web_client_config_from_env()
        if not config:
            raise RuntimeError(
                "No Google OAuth web credentials found. Set GOOGLE_CLIENT_SECRETS to a "
                "downloaded web client_secret.json, OR set GOOGLE_OAUTH_CLIENT_ID and "
                "GOOGLE_OAUTH_CLIENT_SECRET. Create a 'Web application' OAuth client in "
                "Google Cloud Console with the Gmail API and Sheets API enabled, and add "
                f"the callback URL ({redirect}) as an authorized redirect URI."
            )
        flow = Flow.from_client_config(
            config, scopes=auth.SCOPES, redirect_uri=redirect
        )
    return flow


def authorization_url(request_base_url: str | None = None) -> tuple[str, str]:
    """Return (auth_url, state) to redirect the user to Google's consent screen."""
    redirect = redirect_uri(request_base_url)
    flow = _build_flow(redirect)
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",  # force a refresh_token on every connect
    )
    return auth_url, state


def exchange_code(
    code: str,
    request_base_url: str | None = None,
    authorization_response: str | None = None,
):
    """Exchange an authorization code for credentials and persist them.

    Saves to the shared token path (auth.token_path) so the CLI and any future
    `coral sql` runs reuse the same Google session. Returns the credentials.
    """
    redirect = redirect_uri(request_base_url)
    flow = _build_flow(redirect)
    if authorization_response:
        flow.fetch_token(authorization_response=authorization_response)
    else:
        flow.fetch_token(code=code)
    creds = flow.credentials
    auth.save_credentials(creds)
    return creds


def status() -> dict:
    """Headless-safe connection status for the web UI (never opens a browser)."""
    connected = False
    try:
        connected = auth.has_credentials()
    except Exception:
        connected = False
    return {
        "connected": connected,
        "token_path": str(auth.token_path()),
        "scopes": auth.SCOPES,
    }
