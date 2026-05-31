import json
import re

import requests

_BASE_API = "https://www.footmercato.net/api/3.0/articles"
_TIMEOUT = 10


def list_recent_articles(team_id: str) -> list[dict]:
    resp = requests.get(
        _BASE_API,
        headers={"Accept": "application/ld+json"},
        params={
            "articleTeams.footdataTeamId[]": team_id,
            "order[publishedAt]": "desc",
            "isCurrentlyPublished": "true",
        },
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["hydra:member"]


def fetch_article_body(article_id: str, slug: str) -> str:
    url = f"https://www.footmercato.net/a{article_id}-{slug}"
    resp = requests.get(url, timeout=_TIMEOUT)
    resp.raise_for_status()
    for raw in re.findall(
        r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
        resp.text,
        re.DOTALL,
    ):
        data = json.loads(raw)
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict) and "articleBody" in item:
                return item["articleBody"]
    raise ValueError(f"articleBody introuvable pour a{article_id}-{slug}")
