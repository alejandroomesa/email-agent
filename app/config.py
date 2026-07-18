import os
from functools import lru_cache
from pathlib import Path

import yaml

from app.models import Category

APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent

CATEGORIES_PATH = Path(os.environ.get("CATEGORIES_PATH", APP_DIR / "categories.yaml"))
CREDENTIALS_PATH = Path(
    os.environ.get("GMAIL_CREDENTIALS_PATH", PROJECT_DIR / "credentials" / "client_secret.json")
)
TOKEN_PATH = Path(os.environ.get("GMAIL_TOKEN_PATH", PROJECT_DIR / "credentials" / "token.json"))
DB_PATH = Path(os.environ.get("DB_PATH", PROJECT_DIR / "data" / "agent.db"))

OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")
GMAIL_QUERY = os.environ.get("GMAIL_QUERY", "in:inbox is:unread")

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]


@lru_cache
def load_categories() -> list[Category]:
    raw = yaml.safe_load(CATEGORIES_PATH.read_text(encoding="utf-8"))
    return [Category(**entry) for entry in raw["categories"]]
