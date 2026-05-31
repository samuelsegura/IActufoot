import os


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
    }
