import os

# Cascade : le meilleur d'abord ; le dernier (500 requêtes/jour) est le filet de sécurité.
DEFAULT_MODELS = "gemini-4-hydrogen,gemini-3.8-flash,gemini-3.6-flash,gemini-3.5-flash-lite"


def load() -> dict:
    def require(key: str) -> str:
        val = os.environ.get(key)
        if not val:
            raise RuntimeError(f"Variable d'environnement manquante : {key}")
        return val

    return {
        "TELEGRAM_BOT_TOKEN": require("TELEGRAM_BOT_TOKEN"),
        "TELEGRAM_CHAT_ID": require("TELEGRAM_CHAT_ID"),
        "GEMINI_API_KEY": require("GEMINI_API_KEY"),
        "POLL_INTERVAL_MINUTES": int(os.environ.get("POLL_INTERVAL_MINUTES", "15")),
        "GEMINI_MODELS": [
            m.strip() for m in (os.environ.get("GEMINI_MODELS") or DEFAULT_MODELS).split(",") if m.strip()
        ],
        "DB_PATH": os.environ.get("DB_PATH", "data/seen.db"),
    }
