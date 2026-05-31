# actufoot

Autonomous bot that monitors new articles on Footmercato for OM and Barça, summarizes them in 3 bullet points via Gemini AI, and pushes them to a Telegram channel.

## Prerequisites

- Docker + docker compose

## Setup

```bash
cp .env.example .env
# Fill in TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GEMINI_API_KEY
```

## Run

```bash
docker compose up -d
```

## Logs

```bash
docker compose logs -f
```
