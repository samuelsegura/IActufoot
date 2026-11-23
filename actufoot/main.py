import sqlite3
import time
from datetime import datetime

from actufoot import config
from actufoot.footmercato import fetch_article_body, list_recent_articles
from actufoot.store import init_db, is_seen, mark_seen, seed_seen
from actufoot.summarizer import condense_quotes, summarize
from actufoot.telegram import MAX_LEN, format_message, send_message, truncate_body, visible_length
from actufoot.utils import retry

TEAMS = [
    ("OM", "4523010864861042854"),
    ("Barça", "8158115007993136624"),
]


def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


_MARGIN = 100  # marge de sécurité : un modèle compte mal les caractères


def build_text(title: str, url: str, article_body: str, cfg: dict) -> str:
    """Résumé + citations, garanti ≤ 4096 caractères rendus. Ne lève pas pour cause de longueur."""
    key, model = cfg["GEMINI_API_KEY"], cfg["GEMINI_MODEL"]
    budget = MAX_LEN - len(title) - 2 - _MARGIN
    body = retry(lambda: summarize(article_body, key, model))
    if visible_length(title, body) > MAX_LEN:
        log(f"[WARN] message trop long ({visible_length(title, body)}) — condensation des citations")
        try:
            body = retry(lambda: condense_quotes(body, key, model, budget))
        except Exception as e:
            log(f"[WARN] condensation échouée : {type(e).__name__}: {e}")
    if visible_length(title, body) > MAX_LEN:
        log(f"[WARN] encore trop long ({visible_length(title, body)}) — troncature")
        body = truncate_body(body, MAX_LEN - len(title) - 2)
    return format_message(title, url, body)


def run_cycle(conn: sqlite3.Connection, cfg: dict, is_cold: bool) -> None:
    for team_name, team_id in TEAMS:
        try:
            articles = retry(lambda: list_recent_articles(team_id))
            if is_cold:
                seed_seen(conn, [str(a["id"]) for a in articles])
                log(f"{team_name} — cold start, {len(articles)} articles seedés")
                continue
            for article in articles:
                try:
                    article_id = str(article["id"])
                    if is_seen(conn, article_id):
                        continue
                    body = retry(lambda: fetch_article_body(article_id, article["slug"]))
                    url = f"https://www.footmercato.net/a{article_id}-{article['slug']}"
                    text = build_text(article["title"], url, body, cfg)
                    retry(lambda: send_message(cfg["TELEGRAM_BOT_TOKEN"], cfg["TELEGRAM_CHAT_ID"], text))
                    mark_seen(conn, article_id)
                    log(f"{team_name} — envoyé : {article['title']}")
                except Exception as e:
                    log(f"[ERROR] {team_name} — article {article.get('id')} abandonné après 3 tentatives : {type(e).__name__}: {e}")
        except Exception as e:
            log(f"[ERROR] {team_name} — équipe abandonnée après 3 tentatives : {type(e).__name__}: {e}")


def main() -> None:
    cfg = config.load()
    init_db(cfg["DB_PATH"])
    conn = sqlite3.connect(cfg["DB_PATH"])
    log("actufoot démarré")
    while True:
        try:
            cur = conn.execute("SELECT COUNT(*) FROM seen")
            is_cold = cur.fetchone()[0] == 0
            run_cycle(conn, cfg, is_cold)
        except Exception as e:
            log(f"[ERROR] erreur cycle : {type(e).__name__}: {e}")
        time.sleep(cfg["POLL_INTERVAL_MINUTES"] * 60)
