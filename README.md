# 📊 Content Analytics Dashboard

Веб-дашборд на **Streamlit** для аналитики контента (TikTok/YouTube). Войдите
через Google и получите статистику своего YouTube-канала автоматически — либо
загрузите CSV вручную. На выходе: KPI, график просмотров и Топ-5 по лайкам.
**[Посмотреть живое демо в браузере](https://content-analyzer-bottk.streamlit.app/)**

![Скриншот дашборда](assets/screenshot.png)

## Возможности

- **Вход через Google/YouTube** с автоматической выгрузкой статистики канала
  через YouTube Data API v3 (последние 50 видео).
- **Светлая и тёмная тема** с переключателем в сайдбаре; hero-шапка,
  KPI-карточки, вкладки «Обзор/Данные» и стилизованная таблица.
- Загрузка CSV с **автоопределением разделителя** (`,` или `;`) — как запасной
  источник данных.
- **Гибкий парсинг дат**: понимает `дд.мм.гггг` и ISO (`гггг-мм-дд`).
- KPI: количество видео, суммарные просмотры, средний ER.
- Линейный график просмотров по датам (Plotly).
- Горизонтальная гистограмма Топ-5 видео по лайкам.
- Таблица со всеми данными.

**ER** считается как `(Лайки + Комментарии) / Просмотры × 100`.

## Структура проекта

```
content-analyzer/
├── app.py                    # UI, layout, логин-гейт, оркестрация
├── requirements.txt          # Зависимости
├── .streamlit/
│   ├── config.toml           # Настройки темы/layout
│   └── secrets.example.toml  # Шаблон секретов (скопировать в secrets.toml)
├── src/
│   ├── data_loader.py        # Загрузка и валидация CSV
│   ├── metrics.py            # KPI и агрегации
│   ├── charts.py             # Функции построения Plotly-графиков
│   ├── theme.py              # Палитры light/dark, CSS, переключатель темы
│   ├── auth/                 # OAuth 2.0 вход через Google
│   │   ├── oauth.py          # authorization code flow, refresh токенов
│   │   └── session.py        # текущий пользователь в сессии Streamlit
│   ├── db/                   # Хранилище пользователей и токенов
│   │   ├── database.py       # подключение (SQLite/Postgres)
│   │   ├── models.py         # модели User, OAuthToken, OAuthState
│   │   └── crypto.py         # шифрование токенов (Fernet)
│   └── youtube/              # Интеграция с YouTube Data API
│       ├── client.py         # выгрузка видео и статистики
│       └── transform.py      # ответ API -> внутренний DataFrame
├── assets/screenshot.png     # Скриншот интерфейса
└── data/sample.csv           # Пример данных
```

## Установка

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

## Настройка входа через Google / YouTube

Встроенный `st.login()` в Streamlit работает только на аутентификацию через OIDC
и **не даёт access token** для вызовов API, поэтому здесь реализован собственный
OAuth 2.0 authorization code flow (на Authlib).

1. **Google Cloud Console**: создайте проект, включите **YouTube Data API v3**.
2. Настройте **OAuth consent screen** и добавьте себя в **Test users**
   (scope `youtube.readonly` относится к sensitive — до верификации Google
   доступен только тестовым пользователям, до 100 аккаунтов).
3. Создайте **OAuth client ID** типа *Web application* и добавьте
   **Authorized redirect URI**, точно совпадающий с `redirect_uri` из секретов:
   - локально: `http://localhost:8501/`
   - на Streamlit Cloud: `https://<app-name>.streamlit.app/`
4. Скопируйте `.streamlit/secrets.example.toml` в `.streamlit/secrets.toml` и
   заполните `client_id`, `client_secret`, `redirect_uri` и `token_encryption_key`.
   Ключ шифрования можно сгенерировать так:
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

`secrets.toml` добавлен в `.gitignore` — реальные секреты не попадут в репозиторий.

## Хранилище

- Локально по умолчанию используется **SQLite** (`content_analyzer.db`).
- URL можно переопределить секретом `database.url` или переменной окружения
  `DATABASE_URL`.
- На Streamlit Community Cloud файловая система **непостоянна**, поэтому для
  продакшена укажите внешний **Postgres** (Neon/Supabase и т.п.).

OAuth-токены хранятся в БД **в зашифрованном виде** (Fernet).

## Запуск

```bash
streamlit run app.py
```

Откройте браузер по адресу `http://localhost:8501`. Войдите через Google, чтобы
загрузить статистику канала, либо переключитесь на источник «CSV-файл» и
загрузите `data/sample.csv`.

## Формат CSV

Обязательные колонки: `Дата`, `Просмотры`, `Лайки`, `Комментарии`
(`Название` подставляется автоматически из даты, если её нет).
