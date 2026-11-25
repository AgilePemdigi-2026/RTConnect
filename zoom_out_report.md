# Zoom Out Review Report: Migrasi Penuh Layanan AI RTConnect ke Server Kampus (Ollama On-Premise)

**Target:** `docs/designs/migrasi_llm_ollama.md` (`Lines 1..324`)

## Reviewer Status

| Reviewer | Status |
| --- | --- |
| `egm-zoom-out` | completed |
| `egm-inventive-catalyst` | completed |

## Prioritized Findings (Blockers -> Major -> Nits)

### 1. Network Boundary & Architectural Topology Misconception (Client vs Backend Egress) - Severity: Blocker
* **Reviewer Lens:** `egm-zoom-out` & `egm-inventive-catalyst`
* **Affected Scope:** Lines 38-42 (Open Questions), Lines 70-126 (Architecture Diagram & Component Flow)
* **Discrepancy Description**: Open Question 1 (Lines 40-41) posits whether an automatic switching mechanism is required between the local IP (`192.168.88.237`) and the Cloudflare domain (`ollama.ebruar.my.id`) when the application is accessed outside campus WiFi. In the architecture (Lines 71-126), the Flutter mobile client interacts strictly with the Flask backend API routes (`/api/v1/letters/ai-fill` and `/api/v1/chatbot/query`). The mobile client never connects directly to the Ollama server. The backend server operates in a fixed deployment environment; its network egress to Ollama does not change when individual citizen mobile devices connect or disconnect from campus WiFi.
* **Rationale & Recommendation**: Eliminate Open Question 1 and any speculative client/backend auto-switching logic. Define Ollama egress strictly as an infrastructure environment variable (`LLM_BASE_URL`) determined by the backend host's deployment topology. If the backend is hosted outside the campus LAN, configure it with the Cloudflare gateway URL; if inside, configure it with the LAN IP. Clarify this boundary in the architecture.

### 2. Zero-Cloud Invariant Contradiction vs Retained Cloud SDK Runtime Paths - Severity: Blocker
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** Lines 182-185 (Section 4, Invariant 1), Lines 274-276 (Detailed Plan, Target File 4: `ai_fill_service.py`)
* **Discrepancy Description**: Invariant 1 explicitly states: *"Zero Outbound Leak: Tidak ada modul backend yang mengimpor atau memanggil `google.genai` Client maupun endpoint `api.openai.com`. Seluruh pustaka cloud AI dinonaktifkan dalam alur kerja runtime."* However, the detailed implementation plan (Lines 274-276) merely modifies `_call_gemini` to mute secondary fallbacks when `LLM_BASE_URL` is configured, while retaining the top-level `import google.genai` (Lines 29-34 of `ai_fill_service.py`) and the `_call_gemini_api` code path.
* **Rationale & Recommendation**: The design must resolve this architectural contradiction. If 100% on-premise data localization is an immutable system invariant, `ai_fill_service.py` and `config.py` should cleanly isolate or remove runtime imports and dead calling paths to external cloud SDKs, or Invariant 1 should be rephrased accurately to state that external egress is gated at runtime via configuration rather than claiming zero module imports.

### 3. Hardcoded Hostnames and IP Whitelists in Application Code - Severity: Major
* **Reviewer Lens:** `egm-inventive-catalyst` & `egm-zoom-out`
* **Affected Scope:** Lines 98-101, 138-140, 273, 283-284
* **Discrepancy Description**: The design and existing implementation in `tanyart_llm_service.py` hardcode explicit hostnames (`ollama.ebruar.my.id`) and IP literals (`192.168.88.237`) into code validation (`endpoint.hostname in (...)`) and string checks (`'ollama.ebruar.my.id' in base_url`). Deploying to any other IP, staging server, or Docker service name (e.g., `http://ollama:11434/v1`) causes immediate failure (`ValueError: Invalid TanyaRT Ollama configuration`).
* **Rationale & Recommendation**: Apply TRIZ Pattern 2 (Extraction). Decouple transport security and authentication from specific hostnames. If `CF_CLIENT_ID` and `CF_CLIENT_SECRET` are provided in configuration, inject them into HTTP headers regardless of hostname matching. Validate `LLM_BASE_URL` as a well-formed URI rather than whitelisting literal strings and campus IP addresses in source code.
* **Secondary Liabilities**: Setting Cloudflare credentials while targeting an internal IP will send non-harmful custom headers over the LAN.

### 4. Process-Local Concurrency Throttling Flaw in Multi-Worker Deployment - Severity: Major
* **Reviewer Lens:** `egm-inventive-catalyst`
* **Affected Scope:** Lines 89-91, 177-178, 223
* **Discrepancy Description**: Concurrency protection is designed around an in-memory `BoundedSemaphore(2)` and `ThreadPoolExecutor(max_workers=2)` inside `tanyart_llm_service.py`. When deployed under Gunicorn (which forks independent OS worker processes), this semaphore is not shared. N workers will permit $N \times 2$ concurrent connections to the campus Ollama server, defeating the stated concurrency cap of 2 and risking server starvation.
* **Rationale & Recommendation**: Acknowledge that process-local semaphores cannot guarantee cluster-wide GPU load limits. Rely on HTTP 429/503 backpressure signals from Ollama or an upstream gateway (e.g. Nginx rate limiting in front of Ollama), combined with graceful fallback to deterministic retrieval, rather than presenting in-process Python semaphores as an absolute concurrency safeguard.
* **Secondary Liabilities**: Relying on upstream HTTP backpressure requires Ollama or its gateway to emit standard 429/503 response codes under queue saturation.

### 5. Disparate HTTP Client Implementations Across Sibling Services - Severity: Major
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** Lines 132-174 (Section 2, Communication Protocol & Interface Specs)
* **Discrepancy Description**: `ai_fill_service.py` uses high-level `urllib.request.urlopen`, whereas `tanyart_llm_service.py` implements a low-level, bespoke `http.client.HTTPConnection` socket loop with manual buffer slicing (`read(262145)`). Both communicate with the exact same Ollama OpenAI-compatible endpoint. This creates duplicate protocol parsing, diverging error handling, and maintenance overhead.
* **Rationale & Recommendation**: Follow Zoom Out Standard Section 4 (Leverage Existing / Pattern Consistency). Unify the Ollama HTTP interaction into a single shared helper or consistent client pattern across both services, reducing codebase fragmentation.

### 6. Excessive 15-Second Form Fill Timeout Blocks Mobile UX - Severity: Major
* **Reviewer Lens:** `egm-zoom-out` & `egm-inventive-catalyst`
* **Affected Scope:** Lines 155, 222, 244
* **Discrepancy Description**: The design allocates a 15.0-second timeout (`Config.LLM_TIMEOUT_SECONDS`) for the form-fill assistant, whereas TanyaRT has a 4.5-second budget. If the campus Ollama server is queued or experiencing high load, a resident waiting on the form-fill screen will experience a 15-second frozen UI before the system falls back to saved profile data (`sumber: 'tersimpan'`).
* **Rationale & Recommendation**: In accordance with mobile UX principles and beforehand cushioning (TRIZ Pattern 4), reduce `LLM_TIMEOUT_SECONDS` to an interactive budget (e.g., 6.0–8.0 seconds), or allow earlier graceful fallback to saved demographic data so residents are not subjected to severe blocking delays on a mobile device.

### 7. Altitude Drop into Implementation Weeds (Regex and Private Helper Names) - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** Lines 180, 271-285
* **Discrepancy Description**: The design document includes low-level code implementation details such as the exact regex pattern `re.sub(r"<think>.*?(?:</think>|$)", "", answer, flags=re.S)` in the architectural invariants section, as well as naming private helper functions (`_call_openai_compatible`, `_call_gemini`, `_settings`). Per the Zoom Out standard, architectural documents should maintain altitude, focusing on component interfaces and data flows rather than low-level script mechanics.
* **Rationale & Recommendation**: Elevate the altitude in the architectural overview. Describe the mechanism as "reasoning tag stripping" and "URL route normalization" rather than embedding Python snippet mechanics in high-level design specifications.

### 8. Redundant Configuration Variable Duplication - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** Lines 241-247, 262-265
* **Discrepancy Description**: Maintaining `TANYART_LLM_BASE_URL` alongside `LLM_BASE_URL`, and `TANYART_LLM_MODEL` alongside `LLM_MODEL`, creates unnecessary cognitive load and potential configuration drift, despite both pointing to the exact same campus instance.
* **Rationale & Recommendation**: While backward compatibility inheritance is sensible, the design should explicitly recommend `LLM_BASE_URL` as the primary unified parameter, treating `TANYART_*` overrides as optional edge-case overrides rather than required parallel variables in documentation and `.env.example`.
