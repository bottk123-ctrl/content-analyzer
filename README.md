# 📊 Content Analytics Dashboard

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![OAuth 2.0](https://img.shields.io/badge/OAuth-2.0-4285F4?logo=google&logoColor=white)](#google--youtube-sign-in-setup)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Live demo](https://img.shields.io/badge/demo-live-brightgreen)](https://content-analyzer-bottk.streamlit.app/)

A **Streamlit** web dashboard for **YouTube / TikTok content analytics**.
Sign in with Google to pull your YouTube channel stats automatically — or upload a
CSV manually. The result: KPI cards, a views timeline, and a Top-5-by-likes chart.

**[▶ Open the live demo](https://content-analyzer-bottk.streamlit.app/)**

![Dashboard screenshot](assets/screenshot.png)

## ✨ Features

- **Google / YouTube sign-in** — automatically fetches the last 50 videos of your
  channel via the YouTube Data API v3.
- **Light & dark themes** with a sidebar toggle — hero header, KPI cards,
  "Overview / Data" tabs, and a styled table.
- **CSV upload** with automatic delimiter detection (`,` or `;`) as a fallback
  data source.
- **Flexible date parsing** — understands `dd.mm.yyyy` and ISO (`yyyy-mm-dd`).
- **KPIs:** video count, total views, average ER.
- **Views-over-time** line chart (Plotly).
- **Top-5 videos by likes** horizontal bar chart.
- **Full data table.**

> **ER** (engagement rate) is computed as `(Likes + Comments) / Views × 100`.

## 🏗 Architecture

```
content-analyzer/
├── app.py                    # UI, layout, login gate, orchestration
├── requirements.txt          # dependencies
├── .streamlit/
│   ├── config.toml           # theme / layout settings
│   └── secrets.example.toml  # secrets template (copy to secrets.toml)
├── src/
│   ├── data_loader.py        # CSV loading & validation
│   ├── metrics.py            # KPIs and aggregations
│   ├── charts.py             # Plotly chart builders
│   ├── theme.py              # light/dark palettes, CSS, theme toggle
│   ├── auth/                 # Google OAuth 2.0
│   │   ├── oauth.py          # authorization code flow, token refresh
│   │   └── session.py        # current user in the Streamlit session
│   ├── db/                   # user & token storage
│   │   ├── database.py       # connection (SQLite / Postgres)
│   │   ├── models.py         # User, OAuthToken, OAuthState models
│   │   └── crypto.py         # token encryption (Fernet)
│   └── youtube/              # YouTube Data API integration
│       ├── client.py         # fetch videos & statistics
│       └── transform.py      # API response -> internal DataFrame
├── assets/screenshot.png     # UI screenshot
└── data/sample.csv           # sample data
```

**Stack:** `Python` · `Streamlit` · `Plotly` · `Pandas` · `Authlib` · `SQLAlchemy` · `Fernet`

## 🚀 Quick start

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501. Sign in with Google to load channel stats, or switch
the source to **CSV file** and upload `data/sample.csv`.

## 🔐 Google / YouTube sign-in setup

Streamlit's built-in `st.login()` only performs OIDC authentication and **does not
expose an access token** for API calls, so this app implements its own OAuth 2.0
authorization code flow (via Authlib).

1. **Google Cloud Console** — create a project and enable **YouTube Data API v3**.
2. Configure the **OAuth consent screen** and add yourself to **Test users**
   (`youtube.readonly` is a sensitive scope; before verification it works only for
   test users, up to 100 accounts).
3. Create an **OAuth client ID** of type *Web application* and add an
   **Authorized redirect URI** matching `redirect_uri` in your secrets exactly:
   - local: `http://localhost:8501/`
   - Streamlit Cloud: `https://<app-name>.streamlit.app/`
4. Copy `.streamlit/secrets.example.toml` to `.streamlit/secrets.toml` and fill in
   `client_id`, `client_secret`, `redirect_uri`, and `token_encryption_key`.
   Generate an encryption key with:
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

`secrets.toml` is git-ignored — real secrets never reach the repository.

## 💾 Storage

- Locally uses **SQLite** (`content_analyzer.db`) by default.
- Override the URL via the `database.url` secret or the `DATABASE_URL` env var.
- On Streamlit Community Cloud the filesystem is **ephemeral**, so use an external
  **Postgres** (Neon / Supabase, etc.) in production.

OAuth tokens are stored in the database **encrypted** (Fernet).

## 📄 CSV format

Required columns: `Дата`, `Просмотры`, `Лайки`, `Комментарии`
(`Название` is auto-filled from the date when missing).

## 📜 License

MIT — see [LICENSE](LICENSE).
