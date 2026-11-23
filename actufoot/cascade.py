"""Cascade de modèles Gemini : on commence par le premier, on bascule quand il ne peut plus répondre.

- 429 quota du JOUR  : modèle écarté jusqu'à la remise à zéro, on passe au suivant (sans rejouer) ;
- 429 quota MINUTE   : on attend (≤ 60 s) et on réessaie le MÊME modèle, sans basculer ;
- 503 surcharge      : suivant pour cette requête seulement, modèle non écarté ;
- 404 modèle inconnu : modèle écarté pour la session ([ERROR]), les autres continuent ;
- autre erreur       : remonte telle quelle.
"""
import re
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import google.genai as genai

MAX_MINUTE_WAIT = 60  # s
MAX_MINUTE_TRIES = 2


class AllModelsExhausted(Exception):
    """Aucun modèle de la cascade ne peut répondre maintenant."""


def _error_items(exc: Exception) -> list[dict]:
    d = getattr(exc, "details", None)
    if isinstance(d, dict):
        d = d.get("error", d)
        items = d.get("details", []) if isinstance(d, dict) else []
        return [i for i in items if isinstance(i, dict)]
    return []


def _retry_delay(items: list[dict]) -> float | None:
    for i in items:
        m = re.fullmatch(r"([\d.]+)s", str(i.get("retryDelay", "")))
        if m:
            return float(m.group(1))
    return None


def classify(exc: Exception) -> tuple[str, float | None]:
    """→ (`day` | `minute` | `overload` | `notfound` | `other`, délai conseillé par Google en secondes)."""
    code = getattr(exc, "code", None)
    items = _error_items(exc)
    if code == 429:
        quota_ids = [str(v.get("quotaId", "")) for i in items for v in i.get("violations", []) if isinstance(v, dict)]
        if any("PerDay" in q for q in quota_ids):
            return "day", _retry_delay(items)
        if any("PerMinute" in q for q in quota_ids):
            return "minute", _retry_delay(items)
        return "other", None
    if code == 503:
        return "overload", None
    if code == 404:
        return "notfound", None
    return "other", None


def _next_pacific_midnight(now: float) -> float:
    """Repli quand Google ne donne pas de délai : minuit heure du Pacifique (reset du quota jour)."""
    try:
        tz = ZoneInfo("America/Los_Angeles")
    except ZoneInfoNotFoundError:
        return now + 3600  # pas de base de fuseaux : on retente toutes les heures
    local = datetime.fromtimestamp(now, tz)
    midnight = (local + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return midnight.timestamp()


class Cascade:
    def __init__(self, models: list[str], api_key: str, log=print, call=None, clock=time.time, sleep=time.sleep):
        self.models = list(models)
        self.log = log
        self._clock, self._sleep = clock, sleep
        self._call = call or self._real_call
        self._client = None
        self._api_key = api_key
        self.exhausted_until: dict[str, float] = {}

    def _real_call(self, model: str, system: str, contents: str) -> str:
        if self._client is None:
            self._client = genai.Client(api_key=self._api_key)
        response = self._client.models.generate_content(
            model=model,
            contents=contents,
            config=genai.types.GenerateContentConfig(system_instruction=system),
        )
        return response.text.strip()

    def generate(self, system: str, contents: str) -> tuple[str, str]:
        """→ (texte, modèle utilisé). Lève AllModelsExhausted si aucun modèle ne peut répondre."""
        for model in self.models:
            if self.exhausted_until.get(model, 0) > self._clock():
                continue
            minute_tries = 0
            while True:
                try:
                    return self._call(model, system, contents), model
                except Exception as e:
                    kind, delay = classify(e)
                    if kind == "day":
                        until = self._clock() + delay if delay else _next_pacific_midnight(self._clock())
                        self.exhausted_until[model] = until
                        self.log(f"[WARN] {model} : quota du jour épuisé, écarté jusqu'à "
                                 f"{datetime.fromtimestamp(until):%Y-%m-%d %H:%M} → modèle suivant")
                        break
                    if kind == "minute":
                        if minute_tries >= MAX_MINUTE_TRIES:
                            raise
                        minute_tries += 1
                        wait = min(delay or MAX_MINUTE_WAIT, MAX_MINUTE_WAIT)
                        self.log(f"[WARN] {model} : quota à la minute, attente {wait:.0f} s puis nouvel essai")
                        self._sleep(wait)
                        continue
                    if kind == "overload":
                        self.log(f"[WARN] {model} : surchargé (503) → modèle suivant pour cette requête")
                        break
                    if kind == "notfound":
                        self.exhausted_until[model] = float("inf")
                        self.log(f"[ERROR] {model} : modèle introuvable (404), écarté pour cette session → modèle suivant")
                        break
                    raise
        raise AllModelsExhausted("aucun modèle disponible (quota jour épuisé, surcharge ou introuvable)")
