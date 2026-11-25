# Backend Business Logic Services

## Overview
Domain business services executing the core logic of RTConnect. Encompasses letter generation, PDF compilation, AI-assisted form pre-filling, lexical RAG chatbot ranking, PIN-guarded digital signing, user profile persistence, file storage abstraction (local/S3), and push notification dispatch.

## Interface
- `user_service.py`: Identity and profile queries.
  - `find_by_identity(identity: str) -> dict | None`: Resolves user by email or NIK.
  - `get_user(role: str, user_id: int) -> dict | None`: Fetches user record and normalizes role.
  - `nik_or_email_taken(nik: str, email: str) -> bool`: Checks uniqueness for citizen registration.
  - `update_user_profile(...)`, `update_user_signature(...)`, `update_user_avatar(...)`, `update_user_fcm_token(...)`: Profile and asset mutation helpers.
- `rag_service.py`: Production runtime conversational retrieval engine.
  - `get_knowledge_chunks(force_refresh: bool = False) -> list[dict]`: Caches knowledge records in memory.
  - `compute_cosine_similarity(vec1: dict, vec2: dict) -> float`: Computes lexical cosine similarity.
  - `calculate_kerja_bakti_calendar(query: str, ref_date: date = None) -> dict`: Calculates neighborhood schedule queries deterministically.
- `chatbot_rules.py`: Indonesian NLP normalization, tokenization, topic extraction, and administration scope filtering.
- `ai_fill_service.py`: LLM-assisted form parsing extracting structured demographic JSON from conversational user descriptions with sensitive data masking.
- `ai_draft_service.py`: Template-based official letter content assembly (`build_letter_fields`, `generate_letter_draft`).
- `pdf_service.py`: ReportLab document builder compiling official letters into branded PDF documents (`generate_official_letter_pdf`) with QR verification badges and RT signature overlays.
- `letter_number_service.py`: Atomic sequential letter number generator producing formatted administrative codes (`generate_unique_letter_number`).
- `pin_guard_service.py`: Rate-limited bcrypt verification for RT digital signing PINs (`verify_signing_pin`, `reset_pin_attempts`).
- `file_storage.py`: Abstracted storage engine supporting local private disk storage (`backend/uploads`) or S3-compatible private buckets (`store_bytes`, `read_bytes`, `store_upload`).
- `notification_service.py`: In-app notification dispatcher (`add_notification`) with automatic push notification triggering.
- `push_notification_service.py`: Firebase Cloud Messaging (FCM) integration delivering unicast and multicast mobile push notifications (`send_push_notification`, `send_multicast_notification`).
- `applicant_data.py`: Form validation, parsing, and serialization for letter applicant demographic data.
- `letter_guidance.py`: Requirement and procedure lookup for official letter categories.
- `semantic_embedding_service.py` & `tanyart_llm_service.py`: Optional enhancements for semantic chunk search and Gemini-powered answer synthesis with fallback guards.

## Invariants
- Deterministic legal documents: Official letter bodies are generated strictly from static templates in `ai_draft_service.py`; LLMs are never used to hallucinate letter text.
- PIN protection: `pin_guard_service.py` enforces a maximum failure threshold and lockout duration to prevent brute-force attacks against `RT_SIGNING_PIN_HASH`.
- File path security: `file_storage.py` sanitizes keys to block directory traversal (`..`) and restricts upload extensions to allowed MIME types.
- Resilient chatbot runtime: `rag_service.py` must run autonomously without external LLM dependencies, falling back cleanly to curated responses or WhatsApp contact redirection when queries fall below confidence thresholds.

## Side Effects
- Database reads and writes across all operational tables.
- File system reads and writes to `backend/uploads` (local) or AWS S3 API calls (production).
- Network HTTP/TLS calls to Firebase Cloud Messaging (push notifications) and Google Gemini / OpenAI (form extraction and optional synthesis).

## Verification
- Run: `cd backend && python test_api.py`
