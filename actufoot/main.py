import sqlite3
import time
from datetime import datetime

from actufoot import config
from actufoot.cascade import AllModelsExhausted, Cascade
from actufoot.footmercato import LiveArticle, fetch_article_body, list_recent_articles
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


def build_text(title: str, url: str, article_body: str, cascade: Cascade) -> tuple[str, str]:
    """→ (message, modèles utilisés). Résumé + citations, garanti ≤ 4096 caractères rendus."""
    budget = MAX_LEN - len(title) - 2 - _MARGIN
    body, model = summarize(article_body, cascade)
    used = model
    if visible_length(title, body) > MAX_LEN:
        log(f"[WARN] message trop long ({visible_length(title, body)}) — condensation des citations")
        try:
            body, cmodel = condense_quotes(body, cascade, budget)
            if cmodel != model:
                used = f"résumé: {model}, condensation: {cmodel}"
        except Exception as e:
            log(f"[WARN] condensation échouée : {type(e).__name__}: {e}")
    if visible_length(title, body) > MAX_LEN:
        log(f"[WARN] encore trop long ({visible_length(title, body)}) — troncature")
        body = truncate_body(body, MAX_LEN - len(title) - 2)
    return format_message(title, url, body), used


def _fetch_body(article_id: str, slug: str) -> str | None:
    """Corps de l'article, ou None pour un direct (que `retry` ne doit pas rejouer)."""
    try:
        return fetch_article_body(article_id, slug)
    except LiveArticle:
        return None


def run_cycle(conn: sqlite3.Connection, cfg: dict, cascade: Cascade, is_cold: bool) -> None:
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
                    body = retry(lambda: _fetch_body(article_id, article["slug"]))
                    if body is None:
                        mark_seen(conn, article_id)
                        log(f"{team_name} — direct ignoré : {article['title']}")
                        continue
                    url = f"https://www.footmercato.net/a{article_id}-{article['slug']}"
                    text, used = build_text(article["title"], url, body, cascade)
                    retry(lambda: send_message(cfg["TELEGRAM_BOT_TOKEN"], cfg["TELEGRAM_CHAT_ID"], text))
                    mark_seen(conn, article_id)
                    log(f"{team_name} — envoyé [{used}] : {article['title']}")
                except AllModelsExhausted as e:
                    log(f"[WARN] {team_name} — article {article.get('id')} retenté plus tard : {e}")
                except Exception as e:
                    log(f"[ERROR] {team_name} — article {article.get('id')} abandonné après 3 tentatives : {type(e).__name__}: {e}")
        except Exception as e:
            log(f"[ERROR] {team_name} — équipe abandonnée après 3 tentatives : {type(e).__name__}: {e}")


def main() -> None:
    cfg = config.load()
    init_db(cfg["DB_PATH"])
    conn = sqlite3.connect(cfg["DB_PATH"])
    cascade = Cascade(cfg["GEMINI_MODELS"], cfg["GEMINI_API_KEY"], log=log)
    log(f"actufoot démarré — cascade : {' → '.join(cfg['GEMINI_MODELS'])}")
    while True:
        try:
            cur = conn.execute("SELECT COUNT(*) FROM seen")
            is_cold = cur.fetchone()[0] == 0
            run_cycle(conn, cfg, cascade, is_cold)
        except Exception as e:
            log(f"[ERROR] erreur cycle : {type(e).__name__}: {e}")
        time.sleep(cfg["POLL_INTERVAL_MINUTES"] * 60)
