"""Tests purs de la cascade (faux appels, horloge et sleep injectés). Lancer : python test_cascade.py"""
from actufoot.cascade import AllModelsExhausted, Cascade, classify
from actufoot.summarizer import condense_quotes, summarize


class Err(Exception):
    def __init__(self, code, quota_id=None, delay=None):
        self.code = code
        items = []
        if quota_id:
            items.append({"@type": "type.googleapis.com/google.rpc.QuotaFailure", "violations": [{"quotaId": quota_id}]})
        if delay:
            items.append({"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": f"{delay}s"})
        self.details = {"error": {"code": code, "details": items}}


DAY = lambda delay=74923: Err(429, "GenerateRequestsPerDayPerProjectPerModel-FreeTier", delay)
MIN = lambda: Err(429, "GenerateRequestsPerMinutePerProjectPerModel-FreeTier", 12)


def make(models, script):
    """script[modèle] = liste d'erreurs (levées dans l'ordre) puis réponse normale."""
    calls, sleeps, logs, t = [], [], [], [1000.0]
    queues = {m: list(script.get(m, [])) for m in models}

    def call(model, system, contents):
        calls.append(model)
        if queues[model]:
            raise queues[model].pop(0)
        return f"réponse {model}"

    c = Cascade(models, "k", log=logs.append, call=call, clock=lambda: t[0], sleep=sleeps.append)
    return c, calls, sleeps, logs, t


M = ["a", "b", "c"]

# classify
assert classify(DAY()) == ("day", 74923.0)
assert classify(MIN()) == ("minute", 12.0)
assert classify(Err(503)) == ("overload", None)
assert classify(Err(404)) == ("notfound", None)
assert classify(Err(429))[0] == "other" and classify(ValueError("x"))[0] == "other"

# 1. 429 jour : bascule, modèle écarté (non rappelé ensuite)
c, calls, sleeps, logs, t = make(M, {"a": [DAY()]})
assert c.generate("s", "x") == ("réponse b", "b") and calls == ["a", "b"]
assert c.generate("s", "x") == ("réponse b", "b") and calls == ["a", "b", "b"], calls  # a pas rappelé
assert not sleeps and any("quota du jour" in l for l in logs)

# 2. 429 minute : attente, MÊME modèle, pas de bascule
c, calls, sleeps, logs, t = make(M, {"a": [MIN()]})
assert c.generate("s", "x") == ("réponse a", "a") and calls == ["a", "a"] and sleeps == [12.0]
# plafond 60 s, et au-delà de 2 essais l'erreur remonte sans basculer
c, calls, sleeps, logs, t = make(M, {"a": [Err(429, "XPerMinuteY", 500)] * 3})
try:
    c.generate("s", "x"); raise SystemExit("aurait dû lever")
except Err:
    pass
assert calls == ["a", "a", "a"] and sleeps == [60, 60], (calls, sleeps)

# 3. 503 : suivant pour cette requête, modèle NON écarté
c, calls, sleeps, logs, t = make(M, {"a": [Err(503)]})
assert c.generate("s", "x")[1] == "b"
assert c.generate("s", "x")[1] == "a" and calls == ["a", "b", "a"], calls

# 4. retour au premier après la remise à zéro
c, calls, sleeps, logs, t = make(M, {"a": [DAY(100)]})
assert c.generate("s", "x")[1] == "b"
t[0] += 99
assert c.generate("s", "x")[1] == "b"   # pas encore remis à zéro
t[0] += 2
assert c.generate("s", "x")[1] == "a"   # remis à zéro : le premier reprend la tête

# 5. tous épuisés : AllModelsExhausted, aucun appel superflu ensuite
c, calls, sleeps, logs, t = make(M, {m: [DAY()] for m in M})
try:
    c.generate("s", "x"); raise SystemExit("aurait dû lever")
except AllModelsExhausted:
    pass
n = len(calls)
try:
    c.generate("s", "x"); raise SystemExit("aurait dû lever")
except AllModelsExhausted:
    pass
assert len(calls) == n == 3

# 6. la condensation passe par la même cascade (modèle écarté par le résumé non rappelé)
c, calls, sleeps, logs, t = make(M, {"a": [DAY()]})
_, m1 = summarize("article", c)
_, m2 = condense_quotes("msg", c, 500)
assert (m1, m2) == ("b", "b") and calls == ["a", "b", "b"], calls

# 7. 404 : écarté pour la session ([ERROR]), les autres continuent ; autre erreur : remonte
c, calls, sleeps, logs, t = make(M, {"a": [Err(404)]})
assert c.generate("s", "x")[1] == "b" and c.generate("s", "x")[1] == "b" and calls == ["a", "b", "b"]
assert any("[ERROR]" in l for l in logs)
c, calls, *_ = make(M, {"a": [ValueError("réseau")]})
try:
    c.generate("s", "x"); raise SystemExit("aurait dû lever")
except ValueError:
    assert calls == ["a"]
print("OK")
