# Customer Support AI Platform – TODOs

- [ ] Initialize Django project with apps: `channels_app`, `conversation_app`, `agents_app`, `customers_app`, `commerce_app`, `knowledge_app`, `llm_app`, `analytics_app`, `admin_app`; wire DRF, Celery, Redis, Postgres; env-based settings and RBAC roles.
- [ ] Add optional multi-tenant plumbing (`tenant_id` on major models) and row-level security middleware.
- [ ] Define base models and migrations: Customer, CustomerIdentity (unique channel/external_id), Conversation, Message, AgentProfile, Order, Ticket, PaymentIntent/Transaction, KnowledgeDocument, UserMemorySummary, FollowUpTask; include JSONB metadata fields and timestamps.
- [ ] Set up LLM Router microservice with `/llm/infer` contract; implement vLLM backend first; stubs for llama.cpp server and Ollama; JSON tool schema validation + allow-list per AgentProfile.
- [ ] Build webhook endpoints: `/webhooks/whatsapp` (GET verify hub.challenge, POST normalize text/media/voice, enqueue ASR), `/webhooks/messenger`, `/webhooks/shopify` (HMAC validate, upsert Customer/Order), `/webhooks/magento` (secret validate, upsert), `/webhooks/generic`; add idempotency keys, HMAC/IP allow-list, HTTPS enforcement.
- [ ] Implement outbound senders: WhatsApp Cloud API messages (text/audio), FB `/me/messages`; placeholders for email/SMS.
- [ ] Conversation orchestrator: identity resolution, conversation lifecycle, persist inbound Message, build ContextBundle (profile, summaries, orders, tickets, channel, language, agent config), RAG retrieve docs, call LLM Router, execute tool calls, persist outbound Message, send via channel adapter; audit tool calls and enforce confirmations for financial actions.
- [ ] RAG layer: ingestion jobs to chunk/embed docs (FAQs, product, policies), store metadata/tags, build retriever; coverage reporting for “no relevant docs.”
- [ ] Voice pipeline: media download + object storage, Celery ASR (Whisper) to fill Message.text; TTS (Piper/Coqui) for audio replies on supported channels.
- [ ] Dashboard (React/Vue SPA on DRF): Live Inbox (message stream, tool logs, profile/orders/tickets sidebars, human override), Customer 360 (search, timeline, quick actions), Agent Management (CRUD, prompt versioning/diff, tool toggles, routing rules), Knowledge upload/ingest UI + coverage, Analytics (resolution/deflection/AHT/token usage/tool frequency/payment conversion comparisons), Safety/Compliance audit export.
- [ ] Security & privacy: PII masking in logs, at-rest encryption (DB, object store keys), secrets in vault, per-tenant/channel rate limits, no outbound to external LLMs beyond allowed services.
- [ ] Observability/Ops: logging (ELK/Loki), metrics (Prometheus/Grafana), traces; label by channel/agent/model; Celery queues split (webhook-fast, llm, embeddings, payments) with retries/DLQ.

## Phased plan

- [ ] Phase 0 – Infra/skeleton: base settings, core models/migrations, Celery + Redis wiring, Postgres connection, LLM Router stub (vLLM), basic health checks.
- [ ] Phase 1 – Single-channel text pilot: WhatsApp webhook + outbound text, minimal orchestrator with one Agent and tools (`get_customer_profile`, `create_ticket`), simple Live Inbox UI.
- [ ] Phase 2 – Ecommerce: Shopify/Magento webhooks + sync, commerce/payment tools (`list_customer_orders`, `refund_order`, `create_payment_intent`, `schedule_followup`), RAG over FAQs/products, personalization ContextBundle.
- [ ] Phase 3 – Voice + multi-LLM: ASR/TTS for WhatsApp voice notes, add Ollama and llama.cpp backends with routing policy, hardened JSON tool calling.
- [ ] Phase 4 – Agents + analytics: agent wizard + prompt versioning, full analytics/A-B, audit exports and compliance UI.
