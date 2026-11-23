"""Tests purs (sans réseau) : mise en forme HTML et troncature. Lancer : python test_message.py"""
from actufoot.telegram import MAX_LEN, format_message, truncate_body

# Échappement : titre, corps, URL
msg = format_message('A & B <fin>', 'https://x.net/a1-"z"?a=1&b=2', 'x < y & "z"')
assert msg.startswith('<a href="https://x.net/a1-&quot;z&quot;?a=1&amp;b=2">A &amp; B &lt;fin&gt;</a>'), msg
assert msg.endswith('x &lt; y &amp; "z"'), msg

# Troncature : résumé conservé, citations retirées entières depuis la fin
resume = "• Résumé : " + "Une phrase utile. " * 5
quotes = [f'"{"mot " * 100}{i}" — Jean Dupont' for i in range(10)]
body = resume.strip() + "\n\n• Citations :\n" + "\n".join(quotes)
assert len(body) > MAX_LEN
out = truncate_body(body, 1200)
assert len(out) <= 1200, len(out)
assert out.startswith(resume.strip())
kept = [l for l in out.split("\n") if l.startswith('"')]
assert kept and all(l.endswith("— Jean Dupont") for l in kept), out  # aucune citation coupée
assert kept == quotes[: len(kept)]

# Plus aucune citation ne tient : le bloc entier disparaît, le résumé reste
out = truncate_body(body, 400)
assert "Citations" not in out and out.startswith("• Résumé"), out

# Résumé seul trop long : coupe propre avec « … »
out = truncate_body("• Résumé : " + "abc " * 2000, 500)
assert len(out) <= 500 and out.endswith("…")

# Déjà court : inchangé
assert truncate_body("• Résumé : court", 4096) == "• Résumé : court"
print("OK")
