import google.genai as genai

_SYSTEM = (
    "Tu résumes un article de football en français, de manière factuelle, pour un message Telegram. "
    "Le message a EXACTEMENT ce format, sans introduction ni conclusion :\n\n"
    "• Résumé : <l'objet de l'article, ce qui est nouveau. 1 à 3 phrases. Rien du contexte de "
    "remplissage (rappels de matchs passés, historique du joueur ou du club, stats de fond) "
    "sauf s'il est indispensable pour comprendre la nouveauté.>\n\n"
    "• Citations :\n"
    "\"<citation>\" — <Prénom Nom>\n"
    "\"<citation>\" — <Prénom Nom>\n\n"
    "Règles pour les citations :\n"
    "- Reprends TOUTES les citations directes de l'article, mot pour mot et en entier : "
    "jamais une reformulation, jamais un extrait choisi.\n"
    "- L'auteur est la personne qui parle, pas le média qui a recueilli ses propos.\n"
    "- Une citation par ligne, entre guillemets droits \", suivie de « — » et du nom de l'auteur.\n"
    "- S'il n'y a aucune citation directe dans l'article, n'écris pas le point « Citations » du tout.\n"
    "- Les citations sont toujours complètes, sans aucune coupe ni reformulation, quelle que soit leur longueur."
)

_CONDENSE = (
    "Tu reçois un message Telegram au format « • Résumé : … » suivi de « • Citations : » et d'une "
    "citation par ligne (\"…\" — Prénom Nom). Il est trop long : il doit tenir en {budget} "
    "caractères au maximum. Condense les citations, et elles seules, en COUPANT des passages entiers : "
    "jamais de reformulation, ne réécris, ne remplace et n'ajoute aucun mot, ne change pas l'ordre. "
    "Chaque morceau conservé doit être copié mot pour mot de la citation d'origine. "
    "À chaque endroit où tu retires un passage (début, milieu ou fin), mets […] à sa place. "
    "Ne modifie pas le résumé. Garde le même format. Renvoie uniquement le message condensé."
)


def _generate(system: str, contents: str, api_key: str, model: str) -> str:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=genai.types.GenerateContentConfig(system_instruction=system),
    )
    return response.text.strip()


def summarize(article_body: str, api_key: str, model: str) -> str:
    return _generate(_SYSTEM, article_body, api_key, model)


def condense_quotes(message: str, api_key: str, model: str, budget: int) -> str:
    return _generate(_CONDENSE.format(budget=budget), message, api_key, model)
