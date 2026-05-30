# Connecting Google on the hosted (Vercel) site

The code now supports real Google OAuth on the deployed dashboard: the Google
libraries ship in the function bundle, and the OAuth token is stored in a secure
per-browser cookie instead of the filesystem (which is wiped between serverless
requests). To make the **Connect Google** button work on `coral-con.vercel.app`,
do the one-time setup below.

> **Honest limitation first.** `gmail.readonly` is a Google *restricted* scope.
> Until the OAuth app passes Google's verification (a multi-week review), only
> Google accounts you add as **test users** can connect — everyone else sees an
> "unverified app" warning and is blocked. That's a Google policy, not a code
> issue. For a hackathon this is fine: add your own account (and a judge's, if
> needed) as test users.

---

## 1. Create a Web OAuth client in Google Cloud

1. Google Cloud Console → **APIs & Services → Credentials**.
2. Make sure the **Gmail API** and **Google Sheets API** are enabled
   (APIs & Services → Library).
3. **Create Credentials → OAuth client ID → Application type: Web application**.
4. Under **Authorized redirect URIs**, add exactly:
   ```
   https://coral-con.vercel.app/oauth2callback
   ```
   (Add `http://localhost:8000/oauth2callback` too if you also test locally.)
5. Save. Copy the **Client ID** and **Client secret**.

## 2. Configure the OAuth consent screen

1. APIs & Services → **OAuth consent screen**.
2. User type: **External**. Fill the app name / support email.
3. Add the scopes `.../auth/gmail.readonly` and `.../auth/spreadsheets`.
4. Under **Test users**, add the Google account(s) that will connect on the
   live site. While the app is "Testing", only these accounts can sign in.

## 3. Set environment variables on Vercel

Vercel → project **coral-con** → Settings → **Environment Variables**
(Production). Add:

| Key | Value |
|-----|-------|
| `GOOGLE_OAUTH_CLIENT_ID` | the Web client ID from step 1 |
| `GOOGLE_OAUTH_CLIENT_SECRET` | the Web client secret from step 1 |
| `OAUTH_REDIRECT_URI` | `https://coral-con.vercel.app/oauth2callback` |

Setting `OAUTH_REDIRECT_URI` explicitly avoids any scheme/host mismatch from the
serverless proxy (it must match step 1 exactly).

Then **redeploy** (or push any commit) so the new env vars take effect.

## 4. Try it

1. Open `https://coral-con.vercel.app`, go to the **Import** tab.
2. Click **Connect Google**, sign in with a test-user account, grant access.
3. You're redirected back as connected; the token is stored in a secure
   `cc_gauth` cookie in your browser.
4. Click **Import from Gmail** to pull rejection emails.

## How it works / caveats

- **Token storage:** after consent, the token is kept in an `HttpOnly`, `Secure`,
  `SameSite=Lax` cookie scoped to your browser. The client secret is *not* in the
  cookie — it's injected from the Vercel env vars when refreshing. The token
  auto-refreshes and the cookie updates on each call.
- **Per-browser:** because it's a cookie, each visitor connects their own Google
  account; nobody shares a session.
- **Sheets write-back** on the hosted site needs `SHEETS_SPREADSHEET_ID` set too;
  without it, imported rows still populate the in-memory dashboard view.
- **Local use is unchanged:** locally the CLI/file token flow still works
  (`python -m coralcon.cli gmail-extract`), and that's the most private path —
  your inbox never leaves your machine.
