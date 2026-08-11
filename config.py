import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is not set")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

# Railway Postgres URLs sometimes start with postgres:// — asyncpg needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
