import google.genai as genai

_SYSTEM = (
    "Résume l'article en 3 points maximum, en français, de manière factuelle. "
    "Commence chaque point par •. "
    "Si l'article contient des citations directes pertinentes, intègre-les dans les bullets "
    "sous la forme : • \"Citation exacte\" — Prénom Nom. "
    "Si l'article mentionne l'Olympique de Marseille (OM) ou le FC Barcelone (Barça), "
    "priorise ces informations dans le résumé. "
    "Pas d'introduction ni de conclusion."
)


def summarize(article_body: str, api_key: str) -> str:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=article_body,
        config=genai.types.GenerateContentConfig(system_instruction=_SYSTEM),
    )
    return response.text
