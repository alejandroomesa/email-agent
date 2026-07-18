import os
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv

from app.models import Category

APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent

load_dotenv(PROJECT_DIR / ".env")

CATEGORIES_PATH = Path(os.environ.get("CATEGORIES_PATH", APP_DIR / "categories.yaml"))
DB_PATH = Path(os.environ.get("DB_PATH", PROJECT_DIR / "data" / "agent.db"))

OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")
GMAIL_QUERY = os.environ.get("GMAIL_QUERY", "in:inbox is:unread")

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")


@lru_cache
def load_categories() -> list[Category]:
    raw = yaml.safe_load(CATEGORIES_PATH.read_text(encoding="utf-8"))
    return [Category(**entry) for entry in raw["categories"]]
