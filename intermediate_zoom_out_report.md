# Goldfish Review Report: Intermediate Zoom Out Review
**Target:** `docs/designs/migrasi_llm_ollama.md` (`Lines 1..324`)

## Reviewer Status

| Reviewer | Lens Focus | Status |
| :--- | :--- | :--- |
| `egm-zoom-out` | 10,000-ft High-Altitude Architectural Review & Anti-YAGNI | completed |

---

## Prioritized Findings (Blockers -> Major -> Nits)

### 1. Architectural Identity Crisis & Data Sovereignty Contradiction (On-Premise vs Cloudflare & Supabase) - Severity: 🔴 Blocker
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** Lines 15–22 (The Problem), Lines 36, 94, 185 (Database References), Lines 98–101, 115–121, 216–219 (Cloudflare Access Egress), Lines 184, 274–276 (Zero Outbound Leak vs Cloud SDK)
* **Discrepancy Description**:
  The central high-level mandate of this technical design is "Kemandirian Infrastruktur 100%" and "Kedaulatan Data Warga (UU PDP No. 27/2022)" by eliminating all external third-party cloud egress. However, the architectural design contains three severe contradictions that undermine this 10,000-foot foundation:
  1. *Database contradiction*: The design repeatedly specifies "PostgreSQL / Supabase" as the database storing citizen profiles, whereas RTConnect's authoritative architecture (`AGENTS.md`) is local MySQL. Supabase is an external US cloud BaaS, directly conflicting with on-premise data localization.
  2. *Network egress contradiction*: The design proposes routing citizen letter requests and queries through Cloudflare Access (`ollama.ebruar.my.id`), terminating TLS on external US edge infrastructure, which contradicts the claim that "100% data kependudukan tidak ada yang keluar dari jaringan on-premise".
  3. *Zero-cloud invariant contradiction*: It declares Invariant 1 ("Tidak ada modul backend yang mengimpor google.genai"), while retaining the import and calling routines in `ai_fill_service.py`.
* **Rationale & Recommendation**:
  At the 10,000-foot level, an architecture cannot succeed with conflicting foundational premises. Re-anchor persistence strictly to the existing local MySQL database. Establish a single, coherent network topology: connect the Flask backend to the campus Ollama server over local LAN (or an on-premise VPN/WireGuard tunnel) to preserve strict on-premise data sovereignty. Fully prune dead cloud SDK imports (`google.genai`) to fulfill Invariant 1 cleanly.

### 2. Rejection of Critic's Heavyweight Queue Recommendation in Favor of Minimalist Fail-Soft Architecture (YAGNI & Premature Optimization Defense) - Severity: 🔴 Blocker
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** Lines 176–181 (Section 3: Concurrency & Anti-Overload) & Critic Report Finding 4
* **Discrepancy Description**:
  The Critic Stage proposed introducing a centralized distributed queuing/rate-limiting layer (e.g., Redis queue or central backend gatekeeper) across Gunicorn workers. From a 10,000-foot Zoom Out perspective (Zoom Out Standard Section 2: YAGNI & Premature Optimization), adding an external Redis message broker to RTConnect—a lightweight community RT management application whose current architecture consists solely of Flask, MySQL, and Docker Compose—is a severe architectural anti-pattern and premature optimization.
  Concurrently, the design's current mechanism (`BoundedSemaphore(2)` in `tanyart_llm_service.py`) is an in-process illusion that fails under Gunicorn multi-worker deployments while leaving `ai_fill_service` unthrottled.
* **Rationale & Recommendation**:
  Avoid the premature optimization trap of adding Redis/Celery (YAGNI). Instead, adopt a minimalist, robust fail-soft architectural pattern:
  1. Rely on HTTP-level backpressure (Ollama natively queues requests via `OLLAMA_NUM_PARALLEL`, or returns 503/429 under queue saturation).
  2. Enforce an aggressive, unified timeout budget (4.5s for TanyaRT, 6.0s for Form Fill) with instant graceful fallback:
     - TanyaRT immediately serves verbatim regulation chunks from the local deterministic lexical index (`rag_service.py`).
     - Persuratan immediately populates the form using stored citizen profile data from local MySQL (`sumber: 'tersimpan'`).
  3. This achieves 100% user availability, zero hung requests, and zero added infrastructure complexity, adhering directly to the core principle of the Zoom Out Standard.

---

### 3. Disjoint Sibling Architecture & Codebase Duplication (Siloed AI Services) - Severity: 🟡 Major
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** Lines 81–92 (Component Architecture), Lines 130–174 (Communication Protocol), Lines 241–247, 268–286 (Target Files)
* **Discrepancy Description**:
  The design maintains two siloed, disparate architectures for communicating with the exact same on-premise Ollama daemon:
  - `ai_fill_service.py` uses `urllib.request.urlopen`, a 15.0s timeout, JSON object response format, and no concurrency protection.
  - `tanyart_llm_service.py` uses bespoke `http.client.HTTPConnection` socket buffer slicing, a 4.5s budget, plain text response format, and a BoundedSemaphore(2).
  - Configuration variables are duplicated (`LLM_BASE_URL` vs `TANYART_LLM_BASE_URL`, `LLM_MODEL` vs `TANYART_LLM_MODEL`, `LLM_TIMEOUT_SECONDS` vs `TANYART_LLM_TIMEOUT`).
  Both services are Flask backend components calling the identical on-premise Ollama daemon on the exact same server. Maintaining two divergent HTTP client implementations, separate error models, and duplicate configuration parameters creates architectural fragmentation and technical debt.
* **Rationale & Recommendation**:
  Per Zoom Out Standard Section 4 (Leverage Existing / Pattern Consistency), consolidate the interaction with Ollama into a single, shared internal client helper (e.g. `services/ollama_client.py`). The client should standardize URL normalization (`/v1/chat/completions`), error mapping, timeout enforcement, and credential handling. Unify environment variables around `LLM_BASE_URL` and `LLM_MODEL`, with service-specific timeouts as the only variation.

### 4. Inverted Component Sequencing in Persuratan Pipeline Diagram - Severity: 🟡 Major
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** Lines 81–86, 103–107 (Mermaid Architecture Diagram)
* **Discrepancy Description**:
  The Mermaid architecture diagram sequences `Route_Letter --> Masker --> Guard_SOP --> Service_Fill --> Ollama_Direct`.
  Placing `Guard_SOP` ("Verifikasi SOP & Guardrails Anti-Halusinasi") before `Service_Fill` and before `Ollama_Direct` is an architectural inversion. Guardrails verifying anti-hallucination and SOP requirements can only evaluate the *extracted JSON output* generated by the model, not raw citizen narrative before extraction.
* **Rationale & Recommendation**:
  Correct the component pipeline flow in the Mermaid diagram:
  `Route_Letter --> Masker --> Service_Fill --> Ollama_Direct --> Guard_SOP & Validation --> Form Preview`.
  If Ollama fails or times out, the flow branches directly to local MySQL profile autofill.

### 5. UX Latency Asymmetry (15-Second Mobile Freeze) - Severity: 🟡 Major
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** Lines 155, 222, 244
* **Discrepancy Description**:
  TanyaRT enforces a strict 4.5s budget to maintain responsiveness on mobile devices (SLA NFR 5.1). In contrast, the letter assistant allocates a 15.0s timeout (`Config.LLM_TIMEOUT_SECONDS`). During peak campus server load, a citizen on a mobile device will endure a 15-second frozen loading spinner before the system falls back to saved profile data.
* **Rationale & Recommendation**:
  Apply the minimal latency principle and beforehand cushioning by tightening `LLM_TIMEOUT_SECONDS` to 6.0–8.0 seconds. A 3B model (`qwen2.5:3b-instruct`) executes in 1.5–3.0 seconds under normal conditions. If inference exceeds 6.0 seconds, the server is queued or starved, and the application should fail-soft immediately to stored demographic data so the user is not left hanging.

---

### 6. Altitude Drift into Low-Level Implementation Weeds - Severity: 🟢 Nit
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** Lines 180, 271–285
* **Discrepancy Description**:
  The specification drops altitude into script-level implementation mechanics, quoting the exact python regex `re.sub(r"<think>.*?(?:</think>|$)", "", answer, flags=re.S)` in architectural invariants and enumerating private helper functions (`_call_openai_compatible`, `_call_gemini`, `_settings`).
* **Rationale & Recommendation**:
  Per Zoom Out Standard Section 3 (Anti-Weeds), elevate the altitude. High-level design documents should define architectural responsibilities (e.g. "Sanitasi Tag Penalaran Model", "Normalisasi Jalur Endpoint REST") rather than prescribing python regexes and private function names.

### 7. Missing High-Level Network Topology & Deployment Boundaries - Severity: 🟢 Nit
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** Lines 40–41, 66–75, 97–101
* **Discrepancy Description**:
  The architecture groups components into "Klien", "Backend API", and "Server AI On-Premise Kampus" without defining the network deployment boundaries between them. This ambiguity spawned Open Question 1 (asking if mobile clients need to switch between local IP and Cloudflare domain when disconnecting from WiFi), erroneously conflating client-to-backend traffic with backend-to-Ollama egress.
* **Rationale & Recommendation**:
  Add a concise deployment topology statement: The Flask backend is a fixed deployment entity communicating with the campus Ollama server over a designated internal route (LAN or private tunnel). Mobile clients communicate exclusively with the Flask API via HTTPS, remaining completely agnostic of Ollama's network location.
