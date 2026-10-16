# Собачьи тёрки — web-версия

Конфликтная стратегическая игра на 2–4 игроков. Стек: FastAPI + PostgreSQL + Redis + Vue 2.

## Структура

- `backend/` — FastAPI (REST + WebSocket, игровой движок).
- `frontend/` — Vue 2 (Vite), минималистичная SVG/CSS-графика.
- `docker-compose.yml` — PostgreSQL + Redis + backend + frontend.

## Локальный запуск (dev)

Бэкенд (по умолчанию SQLite, работает без внешнего сервера):

    cd backend
    python -m venv .venv
    .venv\Scripts\pip install -r requirements.txt
    .venv\Scripts\python -m app.seed          # залить каталог карт
    .venv\Scripts\uvicorn app.main:app --reload

Фронтенд (проксирует /api на http://localhost:8000):

    cd frontend
    npm install
    npm run dev

Открой http://localhost:5173 — «Фронтенд работает» + «Бэкенд: Бэкенд работает».

## Каталог карт (REST)

Данные — в `backend/app/data/*.json` (см. `data/README.md`). Заливка: `python -m app.seed`.

- `GET /api/catalog/districts` — 13 районов.
- `GET /api/catalog/actions` — 21 действие (13 стандартных + 8 ситуативных).
- `GET /api/catalog/action-cards` — 32 карты действий.
- `GET /api/catalog/events` — 26 событий.
- `GET /api/catalog/gangs` — 16 банд.

## Запуск целиком через Docker

    docker compose up --build

- фронтенд: http://localhost:8080
- бэкенд: http://localhost:8000
- postgres: localhost:5432, redis: localhost:6379

В Docker бэкенд использует PostgreSQL (`DATABASE_URL` задаётся в compose).

## Статус

- Ч0.1 — каркас и «Hello» на обоих концах.
- Ч0.2 — каталог карт в БД + сид из JSON + REST-эндпоинты каталога.