import html

import requests

_TIMEOUT = 10

# Limite Telegram, mesurée sur le texte rendu (balises retirées, entités décodées).
MAX_LEN = 4096
_QUOTE_STARTS = ('"', "«", "“")


def format_message(title: str, url: str, body: str) -> str:
    """Titre cliquable (HTML) puis corps. Titre et corps sont échappés."""
    link = html.escape(url, quote=True)
    return f'<a href="{link}">{html.escape(title, quote=False)}</a>\n\n{html.escape(body, quote=False)}'


def visible_length(title: str, body: str) -> int:
    """Longueur du message rendu par Telegram (titre + 2 sauts de ligne + corps)."""
    return len(title) + 2 + len(body)


def truncate_body(body: str, max_len: int) -> str:
    """Dernier recours : retire les citations entières depuis la fin, puis coupe proprement.

    Le résumé est conservé tant que possible.
    """
    lines = body.strip().split("\n")
    while len("\n".join(lines)) > max_len and lines and lines[-1].lstrip().startswith(_QUOTE_STARTS):
        lines.pop()
        while lines and not lines[-1].strip():
            lines.pop()
    if lines and lines[-1].strip().startswith("• Citations"):
        lines.pop()
        while lines and not lines[-1].strip():
            lines.pop()
    text = "\n".join(lines)
    if len(text) > max_len:
        cut = text[: max_len - 1]
        space = cut.rfind(" ")
        if space > max_len // 2:
            cut = cut[:space]
        text = cut.rstrip() + "…"
    return text


def send_message(token: str, chat_id: str, text: str) -> None:
    """Envoie `text` en HTML : l'appelant fournit un texte déjà échappé (cf. format_message)."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(
        url,
        json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
