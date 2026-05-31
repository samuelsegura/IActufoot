import sqlite3
import time
from datetime import datetime

from actufoot import config
from actufoot.footmercato import fetch_article_body, list_recent_articles
from actufoot.store import init_db, is_seen, mark_seen, seed_seen
from actufoot.summarizer import summarize
from actufoot.telegram import send_message

TEAMS = [
    ("OM", "4523010864861042854"),
    ("Barça", "8158115007993136624"),
]


def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def run_cycle(conn: sqlite3.Connection, cfg: dict, is_cold: bool) -> None:
    for team_name, team_id in TEAMS:
        try:
            articles = list_recent_articles(team_id)
            if is_cold:
                seed_seen(conn, [str(a["id"]) for a in articles])
                log(f"{team_name} — cold start, {len(articles)} articles seedés")
                continue
            for article in articles:
                try:
                    article_id = str(article["id"])
                    if is_seen(conn, article_id):
                        continue
                    body = fetch_article_body(article_id, article["slug"])
                    bullets = summarize(body, cfg["GEMINI_API_KEY"])
                    url = f"https://www.footmercato.net/a{article_id}-{article['slug']}"
                    text = f"{article['title']}\n\n{bullets}\n\n{url}"
                    send_message(cfg["TELEGRAM_BOT_TOKEN"], cfg["TELEGRAM_CHAT_ID"], text)
                    mark_seen(conn, article_id)
                    log(f"{team_name} — envoyé : {article['title']}")
                except Exception as e:
                    log(f"{team_name} — erreur article {article.get('id')}: {e}")
        except Exception as e:
            log(f"{team_name} — erreur équipe : {e}")


def main() -> None:
    cfg = config.load()
    init_db()
    conn = sqlite3.connect("data/seen.db")
    log("actufoot démarré")
    while True:
        try:
            cur = conn.execute("SELECT COUNT(*) FROM seen")
            is_cold = cur.fetchone()[0] == 0
            run_cycle(conn, cfg, is_cold)
        except Exception as e:
            log(f"erreur cycle : {e}")
        time.sleep(cfg["POLL_INTERVAL_MINUTES"] * 60)
