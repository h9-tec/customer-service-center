# Customer Support AI Platform

On-prem, multi-channel customer support backend with Django + DRF, Celery, local LLM router (Ollama/vLLM/llama.cpp), commerce integrations, voice (Whisper/TTS), agent prompt management, analytics, and compliance/audit logging.

## Features
- Channels: WhatsApp Cloud API (text/media/voice), Shopify, Magento; outbound WhatsApp send + TTS audio upload.
- Orchestrator: context-aware replies with tool-calling (orders, payments, follow-ups) and tool allow-lists per agent.
- LLM Router: Ollama/vLLM/llama.cpp backends, optional streaming.
- Voice: Whisper ASR (local HF model), local TTS with media upload to WhatsApp.
- Commerce: Shopify/Magento webhooks with HMAC/secret validation and idempotency checks; commerce tools (list/update orders, payment intents, capture/refund).
- Agents: prompt versioning and rollback, routing rules (channel/language), audit logs on changes.
- Analytics: daily KPIs (resolution/deflection/AHT/tool success/payment conversion), audit logs with CSV export.
- Security/Compliance: API key auth for server-to-server, RBAC (admin on ops endpoints), webhook IP allow-list, throttling, PII masking/encryption (optional), audit for financial actions.
- Metrics: Prometheus counters/histograms for webhooks, LLM calls, ASR/TTS, tool calls, payments.

## Quickstart
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000   # Django
celery -A core worker -l info              # Celery worker
celery -A core beat -l info                # Celery beat (daily KPIs)
uvicorn llm_router.main:app --port 8001    # LLM Router
```

## Environment
Copy `.env.example` → `.env` and set:
- Django: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`
- DB/Redis: `POSTGRES_*`, `CELERY_BROKER_URL`
- WhatsApp: `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_TOKEN`, `WHATSAPP_API_BASE`, `WHATSAPP_APP_SECRET`
- Shopify/Magento: `SHOPIFY_SHARED_SECRET`, `MAGENTO_WEBHOOK_SECRET`
- LLM: `LLM_ROUTER_URL`, `OLLAMA_HOST`, `VLLM_URL`/`VLLM_API_KEY`, `LLAMACPP_URL`
- Voice: `WHISPER_MODEL_ID` (default `openai/whisper-large-v3`), `WHISPER_DEVICE`, `TTS_SERVICE_URL`, `TTS_VOICE`
- Security: `API_KEY` (server-to-server), `WEBHOOK_IP_ALLOWLIST`, `ENCRYPTION_KEY` (Fernet, optional for PII)

## Key Endpoints (admin unless noted)
- Health: `/health`, `/api/health/`
- Webhooks: `/api/webhooks/whatsapp/` (GET verify, POST inbound), `/api/webhooks/shopify/`, `/api/webhooks/magento/`
- Outbound: `/api/webhooks/whatsapp/send/` (auth/API key)
- Agents: `/api/agents/` CRUD, `/api/agents/<id>/prompts/` versions, `/api/agents/<id>/prompts/rollback/`
- Conversations/Messages: `/api/messages/conversations/`, `/api/messages/conversations/<id>/messages/`
- LLM: `/api/llm/tool-calls/`
- Analytics: `/api/analytics/kpi/daily/`, `/api/analytics/audit/`, `/api/analytics/audit/export/`
- Customers: `/api/customers/<id>/timeline/`, `/api/customers/<id>/timeline/export/`
- LLM Router: `/llm/infer` (supports stream flag), `/llm/ollama/models`

## Voice/TTS
- Incoming voice: media download → Whisper ASR → update `Message.text`
- Outbound TTS: text → local TTS HTTP → media upload to WhatsApp → attach media_id

## Commerce Tools (with confirmation safeguards)
- `list_customer_orders`, `update_order_status`
- `create_payment_intent`, `capture_payment_intent`
- `refund_order`
- `schedule_followup`

## Security & Compliance
- RBAC: admin required for ops/analytics/tool logs; API key for server-to-server
- Webhook HMAC/signatures, IP allow-list, throttling
- PII masking and optional encryption (email/phone)
- Audit logs for financial/tools and agent prompt changes; exportable CSV

## Metrics/Observability
Prometheus metrics exposed via `prometheus_client` (integrate with your exporter):
- Webhooks, LLM latency/back-end/model, ASR/TTS latency, tool calls, payments

## Notes
- Streaming: LLM Router supports stream flag; channel adapters can be extended to forward partials.
- Set up Celery beat for daily KPIs.
- Ensure Whisper/TTS services are running locally if voice is enabled.***
