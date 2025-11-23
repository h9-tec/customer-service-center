from prometheus_client import Counter, Histogram

# Webhooks
WEBHOOK_REQUESTS = Counter("webhook_requests_total", "Webhook requests", ["channel", "status"])

# LLM calls
LLM_REQUESTS = Counter("llm_requests_total", "LLM requests", ["backend", "model"])
LLM_LATENCY = Histogram("llm_latency_seconds", "LLM latency", ["backend", "model"])

# ASR/TTS
ASR_REQUESTS = Counter("asr_requests_total", "ASR requests", ["model"])
ASR_LATENCY = Histogram("asr_latency_seconds", "ASR latency", ["model"])
TTS_REQUESTS = Counter("tts_requests_total", "TTS requests", ["voice"])
TTS_LATENCY = Histogram("tts_latency_seconds", "TTS latency", ["voice"])

# Tools
TOOL_CALLS = Counter("tool_calls_total", "Tool calls", ["tool", "success"])

# Payments
PAYMENT_EVENTS = Counter("payment_events_total", "Payment events", ["status"])
