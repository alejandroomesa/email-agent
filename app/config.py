import os
from pathlib import Path

import yaml
from dotenv import load_dotenv, set_key

from app.models import Category

APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent
ENV_PATH = PROJECT_DIR / ".env"

load_dotenv(ENV_PATH)

CATEGORIES_PATH = Path(os.environ.get("CATEGORIES_PATH", APP_DIR / "categories.yaml"))
DB_PATH = Path(os.environ.get("DB_PATH", PROJECT_DIR / "data" / "agent.db"))

OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")
GMAIL_QUERY = os.environ.get("GMAIL_QUERY", "in:inbox is:unread")

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

# Nombres de las variables de entorno editables desde la app de escritorio.
ENV_SETTINGS_KEYS = ("GMAIL_ADDRESS", "GMAIL_APP_PASSWORD", "OLLAMA_MODEL", "GMAIL_QUERY")


def load_categories() -> list[Category]:
    raw = yaml.safe_load(CATEGORIES_PATH.read_text(encoding="utf-8"))
    return [Category(**entry) for entry in raw["categories"]]


def save_categories(categories: list[Category]) -> None:
    payload = {"categories": [c.model_dump() for c in categories]}
    CATEGORIES_PATH.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def save_env_settings(values: dict[str, str]) -> None:
    """Persiste valores en .env y los aplica al proceso actual sin reiniciar."""
    ENV_PATH.touch(exist_ok=True)

    for key in ENV_SETTINGS_KEYS:
        if key not in values:
            continue
        value = values[key]
        set_key(str(ENV_PATH), key, value)
        os.environ[key] = value

    reload_settings()


def reload_settings() -> None:
    global OLLAMA_MODEL, GMAIL_QUERY, GMAIL_ADDRESS, GMAIL_APP_PASSWORD
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")
    GMAIL_QUERY = os.environ.get("GMAIL_QUERY", "in:inbox is:unread")
    GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
    GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
