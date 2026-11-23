# actufoot — Instructions IA

## Fichiers tampons pilotage ↔ exécutant

- `./pilote.md` (racine du repo, gitignored) — le copilote écrit ici les prompts
- `./executant.md` (racine du repo, gitignored) — répondre ici : plan demandé, ou résumé de chaque tâche terminée

Quand Samuel dit **"lis pilote.md"** : lire `./pilote.md` et répondre dans `./executant.md`. Après chaque commit d'étape, y écrire le résumé du livrable (statut, commit, fichiers, points notables), sans attendre de relance. Toujours écraser — fichier frais, un message à la fois.

## Rôle du projet

Bot de veille foot autonome. Surveille les nouveaux articles Footmercato sur
l'OM et le Barça, les résume en 3 bullets via IA, et les pousse sur Telegram.
Démon Python tournant en boucle, packagé en conteneur Docker, déployé sur VPS.

## Stack

- **Python** (≥ 3.12)
- **Docker + docker-compose**, conteneur `restart: unless-stopped`
- **LLM** : Google Gemini, palier gratuit (`GEMINI_API_KEY`), **cascade de modèles**
  (`GEMINI_MODELS`, liste ordonnée, défaut `gemini-4-hydrogen,gemini-3.8-flash,gemini-3.6-flash,gemini-3.5-flash-lite` ;
  quotas gratuits : 20 requêtes/jour par modèle, 500 pour le dernier = filet). `cascade.py` : 429 jour →
  modèle écarté jusqu'au reset ; 429 minute → attente, même modèle ; 503 → suivant sans écarter. SDK `google-genai` — vérifier
  nom/version courants via `ctx7` avant de pinner. Pas de `temperature` (1.0
  recommandé par Google pour Gemini 3+).
- **Dédup** : SQLite (stdlib `sqlite3`), fichier persisté dans un volume Docker.
- **Telegram** : appel HTTP direct à la Bot API (`sendMessage`), pas de lib.

## Conventions

- **Secrets** : `.env` gitignored, `.env.example` versionné avec valeurs vides.
- **Images Docker épinglées** : jamais `latest`.
- **Tout passe par git** : pas de modif ad-hoc sur le VPS, il ne doit pas diverger.
- **Solution la plus simple d'abord.** Pas d'anticipation (ne pas créer de
  fichiers/modules pour une étape ultérieure). Deps minimales.
- **Plan avant code** sur toute tâche non triviale.
- Francophone.

## Architecture cible

Package `actufoot/`, modules à responsabilité isolée :

- `config.py` — lecture/validation des variables d'env au démarrage.
- `footmercato.py` — client API publique (JSON-LD/Hydra, sans auth) :
  - liste des articles récents par équipe via
    `GET https://www.footmercato.net/api/3.0/articles`
    (`Accept: application/ld+json`, filtres `articleTeams.footdataTeamId[]`,
    `order[publishedAt]=desc`, `isCurrentlyPublished=true`) → `hydra:member[]`
    (id, title, slug).
  - contenu d'un article : `GET https://www.footmercato.net/a{id}-{slug}`, extrait
    le `articleBody` du `<script type="application/ld+json">`.
- `cascade.py` — bascule entre modèles Gemini selon la nature de l'erreur (jour / minute / 503 / 404).
- `summarizer.py` — résumé Gemini en français, factuel : « • Résumé » (1 à 3
  phrases, la nouveauté seulement) + « • Citations » (toutes les citations
  directes, mot pour mot, auteur = celui qui parle). `condense_quotes` : second
  appel qui condense les citations si le message dépasse la limite.
- `telegram.py` — message unique en HTML : titre cliquable (lien) + corps.
  Limite 4096 caractères mesurée sur le texte rendu ; jamais de découpe, jamais
  d'échec pour longueur (budget au modèle → condensation → troncature).
- `store.py` — SQLite : `is_seen(id)`, `mark_seen(id)`, `seed_seen(ids)`.
- `main.py` — boucle : par équipe → liste → filtre nouveaux → fetch body →
  résumé → envoi → `mark_seen`, puis `sleep(POLL_INTERVAL_MINUTES)`.

### IDs équipes
- OM : `4523010864861042854`
- Barça : `8158115007993136624`

## Robustesse (non négociable)

- **Cold start** : au 1er run (DB vide), *seed* les IDs actuels SANS les envoyer.
  On ne notifie que ce qui paraît après le démarrage (pas de déversement du backlog).
- **`mark_seen` uniquement après envoi Telegram réussi** : un envoi raté est
  retenté au cycle suivant (pas de perte, pas de doublon).
- **Isolation des erreurs** : try/except par article, par équipe, et autour du
  cycle. La boucle ne meurt jamais — log puis on continue.
- **Directs ignorés** : une page sans `articleBody` portant un JSON-LD `LiveBlogPosting`/`BroadcastEvent`
  est marquée vue sans envoi (log d'info). Toute autre page sans `articleBody` reste une erreur retentée.
- **Timeouts** sur tous les appels HTTP. **Logs sur stdout** (`docker logs`).

## Variables d'environnement

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `GEMINI_API_KEY`
- `POLL_INTERVAL_MINUTES` (défaut 15)
- `GEMINI_MODELS` (liste séparée par virgules, défaut : voir Stack)
