from actufoot.cascade import Cascade

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
    "- Une citation, ce sont des PROPOS TENUS par une personne identifiée (joueur, entraîneur, dirigeant, "
    "arbitre…), d'au moins une phrase. Ne sont PAS des citations : un mot ou une expression isolés entre "
    "guillemets, un qualificatif ou un titre attribué à un média, un surnom. Si un tel mot compte pour "
    "comprendre l'article, il va dans le résumé, jamais dans les citations.\n"
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


def summarize(article_body: str, cascade: Cascade) -> tuple[str, str]:
    """→ (message, modèle utilisé)."""
    return cascade.generate(_SYSTEM, article_body)


def condense_quotes(message: str, cascade: Cascade, budget: int) -> tuple[str, str]:
    """→ (message condensé, modèle utilisé)."""
    return cascade.generate(_CONDENSE.format(budget=budget), message)
