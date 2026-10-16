"""Настройки приложения из переменных окружения."""
import os

# По умолчанию — SQLite (работает без внешнего сервера, удобно для dev и тестов).
# В docker-compose для PostgreSQL задаётся DATABASE_URL=postgresql+asyncpg://...
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./sobachi_terki.db")