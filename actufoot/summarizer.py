import google.genai as genai

_SYSTEM = (
    "Résume le texte en 3 points maximum, en français, de manière factuelle. "
    "Commence chaque point par •. Pas d'introduction ni de conclusion."
)


def summarize(article_body: str, api_key: str) -> str:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=article_body,
        config=genai.types.GenerateContentConfig(system_instruction=_SYSTEM),
    )
    return response.text
