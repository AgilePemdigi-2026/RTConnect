# Consolidated Review Report: EGM Multi-Lens Document Audit

**Target Document:** `docs/designs/migrasi_llm_ollama.md` (`Lines 1..324`)  
**Audit Protocol:** Elephant & Goldfish Model (EGM) Curated Full Review (Stages 5, 6, 7, 8, 9)  
**Date:** 2026-11-25  
**Auditor Swarm:** `egm-zoom-out`, `egm-inventive-catalyst`, `egm-comprehension`, `egm-design`, `egm-structural`, `egm-style`, `egm-implementation-readiness`, `egm-codebase-details`

---

## Executive Summary & Stage Status

The technical design document for migrating RTConnect AI services to an on-premise Ollama campus server has been audited through all five EGM Goldfish review stages in uninterrupted succession.

| Stage | Review Stage Name | Reviewer Personas | Deliverable Artifact | Status |
| :---: | :--- | :--- | :--- | :---: |
| **5** | Initial Zoom Out Review | `egm-zoom-out`, `egm-inventive-catalyst` | [zoom_out_report.md](./zoom_out_report.md) | **Completed** |
| **6** | Comprehension Test | `egm-comprehension` | [comprehension_report.md](./comprehension_report.md) | **Completed** |
| **7** | Critic Review | `egm-design`, `egm-structural`, `egm-style` | [critic_report.md](./critic_report.md) | **Completed** |
| **8** | Intermediate Zoom Out | `egm-zoom-out` | [intermediate_zoom_out_report.md](./intermediate_zoom_out_report.md) | **Completed** |
| **9** | Implementation Readiness | `egm-implementation-readiness`, `egm-codebase-details`, `egm-style` | [implementation_readiness_report.md](./implementation_readiness_report.md) | **Completed** |

### Summary of Audit Findings
Across all 5 review stages, 27 raw findings were discovered. After cross-stage deduplication and thematic synthesis, they are consolidated into **13 actionable remediation items**:
* 🔴 **Blockers**: 5 items (Fatal architectural contradictions, missing mandatory standard sections, or zero-decision failures)
* 🟡 **Majors**: 5 items (System resilience, network boundaries, concurrency flaws, and UX latency risks)
* 🟢 **Nits**: 3 items (Clarity, document conventions, code/path consistency, and style polish)

---

## Consolidated Actionable Items

### 🔴 Critical Blockers

#### ACTION-1: Correct Database Architecture References to Local MySQL
* **Priority:** 🔴 Blocker
* **Affected Scope:** Lines 36, 94, 185
* **Issue:** The document repeatedly refers to the underlying database as `"PostgreSQL / Supabase"` and specifies profile fallback from Supabase. RTConnect's authoritative architecture (`AGENTS.md`) is local MySQL. Citing Supabase (a US cloud BaaS) introduces a factual contradiction to the "100% On-Premise & Data Sovereignty" mandate and misdirects implementers.
* **Remediation:** Replace all mentions of PostgreSQL and Supabase with local MySQL (`Local MySQL Database`). Update the data access references to Flask SQLAlchemy / PyMySQL repositories.

#### ACTION-2: Reconcile Zero-Cloud Invariant with Codebase Modifications
* **Priority:** 🔴 Blocker
* **Affected Scope:** Lines 184, 274–276
* **Issue:** Invariant 1 claims that zero backend modules import or call `google.genai`. However, the implementation plan retains the top-level import and calling path in `ai_fill_service.py`.
* **Remediation:** Either explicitly instruct the removal/isolation of `google.genai` imports and dead functions in `ai_fill_service.py`, or adjust Invariant 1 to accurately specify that outbound cloud calls are strictly gated and disabled via runtime configuration.

#### ACTION-3: Add Mandatory "Risks & Mitigations" Section
* **Priority:** 🔴 Blocker
* **Affected Scope:** Section 3/4 boundary (Lines 188–231)
* **Issue:** The document fails the *Feature Specification Standard* by lacking an explicit `## Risks & Mitigations` section evaluating failure modes and system bounds.
* **Remediation:** Insert a dedicated `## Risks & Mitigations` section explicitly analyzing: (1) Campus server downtime / power outage, (2) GPU VRAM starvation / queuing, (3) Model hallucinations altering demographic data, and (4) Delimiter collisions / prompt injection.

#### ACTION-4: Partition Implementation Plan into Phased Checkpoints
* **Priority:** 🔴 Blocker
* **Affected Scope:** Lines 232–321
* **Issue:** The implementation plan is a flat file list lacking incremental phases, buildability checks, and exit gates, violating the *Implementation Readiness Standard*.
* **Remediation:** Partition the plan into four logical phases:
  - *Phase 1:* Environment & Configuration Unification (`.env`, `.env.example`, `config.py`)
  - *Phase 2:* Service Hardening & Cloud Fallback Cutoff (`ai_fill_service.py`, `tanyart_llm_service.py`, `semantic_embedding_service.py`)
  - *Phase 3:* Integration & SLA Verification (`test_tanyart_full.py`, `ukur_latensi_lengkap.py`, mock letter tests)
  - *Phase 4:* Documentation & Provenance Updates (`concepts_brief.md`, `SITEMAP.md`)

#### ACTION-5: Add Test & Verification Plan for Letter Form Assistant (`ai_fill_service.py`)
* **Priority:** 🔴 Blocker
* **Affected Scope:** Lines 301–321
* **Issue:** The verification plan covers only TanyaRT and compilation, leaving 50% of the modified AI services (`ai_fill_service.py`) with zero test cases.
* **Remediation:** Add concrete test specifications for `ai_fill_service.py`: (1) Valid Ollama extraction and schema validation, (2) Connection timeout and graceful fallback to stored MySQL profile data (`sumber: 'tersimpan'`), and (3) Cloudflare Access header injection when targeting the campus domain.

---

### 🟡 Major Architecture & System Resilience Items

#### ACTION-6: Clarify Network Topology & Eliminate Client-Side Switching Questions
* **Priority:** 🟡 Major
* **Affected Scope:** Lines 40–41, 70–126, 216–218
* **Issue:** Open Question 1 asks if mobile clients need to switch between local IP and Cloudflare when disconnecting from WiFi. Mobile clients communicate solely with the Flask backend API; they never connect to Ollama directly. Furthermore, routing through Cloudflare Access must be explicitly acknowledged as an authorized tunnel boundary or internal LAN IP.
* **Remediation:** Remove Open Question 1. Add a clear deployment boundary explanation stating that Ollama routing is an infrastructure-level configuration on the backend host.

#### ACTION-7: Establish Robust Fail-Soft Concurrency without Heavyweight Queues
* **Priority:** 🟡 Major
* **Affected Scope:** Lines 89–91, 177–180, 223
* **Issue:** `BoundedSemaphore(2)` in `tanyart_llm_service.py` fails under multi-worker Gunicorn processes while leaving `ai_fill_service` unthrottled. Conversely, introducing Redis/Celery is rejected by Zoom Out review as premature optimization (YAGNI).
* **Remediation:** Rely on Ollama native HTTP backpressure (503/429) coupled with aggressive timeouts (4.5s for TanyaRT, 6.0s for Form Fill) and immediate fail-soft fallback (verbatim lexical text for TanyaRT; stored profile autofill for letters).

#### ACTION-8: Invert Pipeline Sequencing in Mermaid Diagram
* **Priority:** 🟡 Major
* **Affected Scope:** Lines 81–86, 103–107
* **Issue:** The architecture diagram places `Guard_SOP` before `Service_Fill` and before `Ollama_Direct`, which is logically inverted since anti-hallucination guardrails can only inspect extracted JSON after model inference.
* **Remediation:** Correct the diagram data flow: `Route_Letter --> Masker --> Service_Fill --> Ollama_Direct --> Guard_SOP & Validation --> Form Preview`.

#### ACTION-9: Unify Disparate HTTP Client Implementations & Prevent `KeyError`
* **Priority:** 🟡 Major
* **Affected Scope:** Lines 132–174, 278–286
* **Issue:** `ai_fill_service.py` uses `urllib`, while `tanyart_llm_service.py` uses low-level `http.client` with raw dictionary access `os.environ["CF_CLIENT_ID"]`, risking unhandled `KeyError`. Code validation also hardcodes literal IP `192.168.88.237`.
* **Remediation:** Align Cloudflare header retrieval using `getattr(Config, 'CF_CLIENT_ID', None)` or `os.environ.get()` defensively across both services. Validate `LLM_BASE_URL` as a standard URI rather than hardcoding IP literals.

#### ACTION-10: Reduce Form-Fill Timeout & Enforce 500ms Inferencing Buffer
* **Priority:** 🟡 Major
* **Affected Scope:** Lines 155, 221–222, 244, 247
* **Issue:** A 15-second timeout for form filling freezes mobile UI during peak server load. Setting `TANYART_LLM_TIMEOUT=5.0` in `.env` leaves zero budget for lexical retrieval within the 5.0s SLA.
* **Remediation:** Reduce `LLM_TIMEOUT_SECONDS` to 6.0–8.0 seconds. Set `TANYART_LLM_TIMEOUT=4.5` in `.env` and `.env.example` to preserve a 500ms buffer for retrieval and formatting.

---

### 🟢 Nits & Document Standards Polish

#### ACTION-11: Differentiate Existing Codebase Baseline from New Delta Tasks
* **Priority:** 🟢 Nit
* **Affected Scope:** Lines 248, 251–286
* **Issue:** Target files list already implemented features (e.g. `192.168.88.237` whitelist) as "Proposed Changes", creating confusion. Directive to "empty or delete" API keys leaves an unapproved choice.
* **Remediation:** Clearly distinguish between verified existing baseline logic and new delta tasks. Explicitly specify setting `GEMINI_API_KEY=` and `OPENAI_API_KEY=` as empty strings.

#### ACTION-12: Standardize Heading Formats, Document Hierarchy & Alternatives Rule
* **Priority:** 🟢 Nit
* **Affected Scope:** Lines 66, 128, 191–210
* **Issue:** Headings mix decimal numbering, letters, and custom prefixes. Alternatives use unlinked author attribution (`Rejected by author:`).
* **Remediation:** Standardize headings to consistent unnumbered H3s. Format alternatives rejection rationales strictly in terms of technical trade-offs without vague author attribution.

#### ACTION-13: Define Acronyms, Expand Abbreviations & Fix Command Paths
* **Priority:** 🟢 Nit
* **Affected Scope:** Lines 27, 48, 186, 217, 306–320
* **Issue:** Undefined terms/acronyms (`SLA NFR 5.1`, `SKD`, `NIK/KK`, `RTC-014`). Verification commands mix `cd backend && python ...` with repo-root paths.
* **Remediation:** Add inline expansions for acronyms and terms. Standardize all verification commands to run from repository root.

---

## Traceability Matrix

This matrix maps each raw finding from the five specialized Goldfish review stages to the consolidated remediation items.

| Raw Finding Source & Identifier | Reviewer Lens | Stage | Consolidated Action Item |
| :--- | :--- | :---: | :--- |
| `zoom_out_report.md` #1 | `egm-zoom-out`, `egm-inventive-catalyst` | Stage 5 | **ACTION-6** (Clarify Network Topology) |
| `zoom_out_report.md` #2 | `egm-zoom-out` | Stage 5 | **ACTION-2** (Reconcile Zero-Cloud Invariant) |
| `zoom_out_report.md` #3 | `egm-inventive-catalyst`, `egm-zoom-out` | Stage 5 | **ACTION-9** (Unify HTTP Client & Remove Hardcoded IPs) |
| `zoom_out_report.md` #4 | `egm-inventive-catalyst` | Stage 5 | **ACTION-7** (Establish Fail-Soft Concurrency) |
| `zoom_out_report.md` #5 | `egm-zoom-out` | Stage 5 | **ACTION-9** (Unify HTTP Client Implementations) |
| `zoom_out_report.md` #6 | `egm-zoom-out`, `egm-inventive-catalyst` | Stage 5 | **ACTION-10** (Reduce Form Timeout to 6-8s) |
| `zoom_out_report.md` #7 | `egm-zoom-out` | Stage 5 | **ACTION-12** (Elevate Altitude / Remove Snippet Weeds) |
| `zoom_out_report.md` #8 | `egm-zoom-out` | Stage 5 | **ACTION-9** (Configuration Unification) |
| `comprehension_report.md` #1 | `egm-comprehension` | Stage 6 | **ACTION-1** (Correct Database References to MySQL) |
| `comprehension_report.md` #2 | `egm-comprehension` | Stage 6 | **ACTION-2** (Zero-Cloud Invariant vs Plan Contradiction) |
| `comprehension_report.md` #3 | `egm-comprehension` | Stage 6 | **ACTION-8** (Inverted Diagram Pipeline Sequencing) |
| `comprehension_report.md` #4 | `egm-comprehension` | Stage 6 | **ACTION-6** (Network Routing & Toplogy Ambiguity) |
| `comprehension_report.md` #5 | `egm-comprehension` | Stage 6 | **ACTION-13** (Define Acronyms: SKD, NFR 5.1, RTC-014) |
| `comprehension_report.md` #6 | `egm-comprehension` | Stage 6 | **ACTION-10** (Timeout Naming & SLA Buffers) |
| `comprehension_report.md` #7 | `egm-comprehension` | Stage 6 | **ACTION-13** (Clarify Path for `concepts_brief.md`) |
| `critic_report.md` #1 | `egm-design`, `egm-structural` | Stage 7 | **ACTION-1** (Inaccurate Database Reference) |
| `critic_report.md` #2 | `egm-structural` | Stage 7 | **ACTION-3** (Missing Mandatory Risks & Mitigations) |
| `critic_report.md` #3 | `egm-structural` | Stage 7 | **ACTION-12** (Violation of Alternatives Attribution Rule) |
| `critic_report.md` #4 | `egm-design` | Stage 7 | **ACTION-7** (Concurrency Starvation between Services) |
| `critic_report.md` #5 | `egm-design` | Stage 7 | **ACTION-6** (Ingress/Egress Privacy & Cloudflare Boundary) |
| `critic_report.md` #6 | `egm-design` | Stage 7 | **ACTION-9** (Missing Cloudflare Headers in TanyaRT Spec) |
| `critic_report.md` #7 | `egm-design` | Stage 7 | **ACTION-3** (Delimiter Sanitization & Prompt Injection) |
| `critic_report.md` #8 | `egm-design` | Stage 7 | **ACTION-7** (Concurrency Wait vs Fail-Soft Fallback) |
| `critic_report.md` #9 | `egm-style` | Stage 7 | **ACTION-12** (Eliminate Glazing, Buzzwords & Colloquialisms) |
| `critic_report.md` #10 | `egm-structural` | Stage 7 | **ACTION-12** (Inconsistent Heading Hierarchy) |
| `critic_report.md` #11 | `egm-style` | Stage 7 | **ACTION-12** (Inconsistent Bilingual Formats) |
| `critic_report.md` #12 | `egm-structural` | Stage 7 | **ACTION-12** (Add Comparative Summary Tables) |
| `intermediate_zoom_out_report.md` #1 | `egm-zoom-out` | Stage 8 | **ACTION-1**, **ACTION-2**, **ACTION-6** (Data Sovereignty) |
| `intermediate_zoom_out_report.md` #2 | `egm-zoom-out` | Stage 8 | **ACTION-7** (Reject Redis Queue / Minimalist Fail-Soft) |
| `intermediate_zoom_out_report.md` #3 | `egm-zoom-out` | Stage 8 | **ACTION-9** (Disjoint Sibling Service Consolidation) |
| `intermediate_zoom_out_report.md` #4 | `egm-zoom-out` | Stage 8 | **ACTION-8** (Inverted Component Sequencing Diagram) |
| `intermediate_zoom_out_report.md` #5 | `egm-zoom-out` | Stage 8 | **ACTION-10** (Form Fill Timeout Cushioning) |
| `intermediate_zoom_out_report.md` #6 | `egm-zoom-out` | Stage 8 | **ACTION-12** (Anti-Weeds / Elevate Architectural Altitude) |
| `intermediate_zoom_out_report.md` #7 | `egm-zoom-out` | Stage 8 | **ACTION-6** (Missing High-Level Network Topology) |
| `implementation_readiness_report.md` #1 | `egm-implementation-readiness` | Stage 9 | **ACTION-4** (Missing Phased Implementation Checkpoints) |
| `implementation_readiness_report.md` #2 | `egm-implementation-readiness` | Stage 9 | **ACTION-5** (Missing Test Plan for `ai_fill_service.py`) |
| `implementation_readiness_report.md` #3 | `egm-codebase-details` | Stage 9 | **ACTION-9** (Config Access Inconsistency & KeyError Risk) |
| `implementation_readiness_report.md` #4 | `egm-codebase-details` | Stage 9 | **ACTION-11** (Distinguish Baseline from Delta Tasks) |
| `implementation_readiness_report.md` #5 | `egm-style`, `egm-codebase-details` | Stage 9 | **ACTION-10** (Align `TANYART_LLM_TIMEOUT=4.5`) |
| `implementation_readiness_report.md` #6 | `egm-implementation-readiness` | Stage 9 | **ACTION-11** (Specify Exact `.env` Directives) |
| `implementation_readiness_report.md` #7 | `egm-codebase-details` | Stage 9 | **ACTION-13** (Standardize Repo-Root Execution Paths) |
| `implementation_readiness_report.md` #8 | `egm-style`, `egm-implementation-readiness` | Stage 9 | **ACTION-4** (Decouple Documentation Provenance Phase) |

---

## Conclusion & Recommended Next Step

The full multi-lens audit is complete. All findings across five review stages have been triaged, deduplicated, and mapped in this consolidated report.

To remediate these findings systematically and bring [migrasi_llm_ollama.md](file:///c:/Users/Dhafin/OneDrive/Desktop/Semester%205/Pengembangan%20Perangkat%20Lunak%20(Prak)/RTConnect/docs/designs/migrasi_llm_ollama.md) to production-ready status, proceed by resolving the five Blockers and five Majors in the target document.
