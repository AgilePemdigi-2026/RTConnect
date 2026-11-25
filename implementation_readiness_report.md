# Goldfish Review Report: Implementation Readiness Test
**Target:** `docs/designs/migrasi_llm_ollama.md` (`Lines 232..324`)

## Reviewer Status

| Reviewer | Status |
| --- | --- |
| `egm-implementation-readiness` | completed |
| `egm-codebase-details` | completed |
| `egm-style` | completed |

## Prioritized Findings (Blockers -> Major -> Nits)

### 1. Missing Phasing & Checkpoints (Violation of Implementation Readiness Standard) - Severity: Blocker
* **Reviewer Lens:** `egm-implementation-readiness`
* **Affected Scope:** `docs/designs/migrasi_llm_ollama.md#L232-L321` (Section: `Detailed Implementation Plan`)
* **Discrepancy Description**: The plan organizes work exclusively as a flat file inventory (`Target Files to Create/Modify` 1–7) followed by test commands. It omits the mandatory "Phasing & Checkpoints" requirement defined in `implementation-readiness-standard.md`. There is no execution ordering, no logical separation of environment configuration from core service refactoring, and no intermediate checkpoints verifying that the codebase remains buildable and stable after each step.
* **Rationale & Recommendation**: The Implementation Readiness standard mandates: *"The plan must partition the work into logical, incremental phases. Each phase must leave the codebase in a stable, buildable, and testable state."*
Partition the plan into explicit phases with concrete entry/exit criteria:
  - **Phase 1: Environment & Configuration Unification** (`backend/.env`, `backend/.env.example`, `backend/config.py`). *Checkpoint:* `python -m py_compile backend/config.py` and environment loading sanity check.
  - **Phase 2: Service Hardening & Cloud Fallback Cutoff** (`backend/services/ai_fill_service.py`, `backend/services/tanyart_llm_service.py`, `backend/services/semantic_embedding_service.py`). *Checkpoint:* Syntax verification and stub tests for local Ollama invocation and profile fallback.
  - **Phase 3: Integration & SLA Verification** (`backend/test_tanyart_full.py`, `backend/ukur_latensi_lengkap.py`). *Checkpoint:* 26/26 retrieval regression tests pass, SLA response time <= 5.0s.
  - **Phase 4: Design Documentation Provenance** (`concepts_brief.md`).

---

### 2. Missing Test & Verification Plan for `ai_fill_service.py` - Severity: Blocker
* **Reviewer Lens:** `egm-implementation-readiness`
* **Affected Scope:** `docs/designs/migrasi_llm_ollama.md#L301-L321` (Section: `Verification Plan`)
* **Discrepancy Description**: The Verification Plan focuses exclusively on TanyaRT suites (`test_tanyart_full.py` and `ukur_latensi_lengkap.py`) and a basic `py_compile` check. It provides zero test cases or verification commands for `ai_fill_service.py` (the Form Fill Assistant), leaving 50% of the modified AI services untested.
* **Rationale & Recommendation**: The plan modifies critical behavior in `ai_fill_service.py` (OpenAI URL normalization, Cloudflare Access headers injection, and disabling cloud fallback to enforce stored profile fallback). Leaving this unverified violates the Zero-Decision Rule and the standard's Test Plan requirement.
Add concrete test cases to the Verification Plan:
  1. **Ollama Form Extraction Test**: Mock HTTP 200 JSON chat completion from Ollama and verify field extraction and schema validation.
  2. **Fail-Safe Fallback Test**: Simulate Ollama connection failure/timeout and verify that `suggest_application` catches the error and cleanly populates fields with `sumber: 'tersimpan'` without failing citizen request.
  3. **Cloudflare Header Injection Test**: Verify that requests targeting `ollama.ebruar.my.id` inject `CF-Access-Client-Id` and `CF-Access-Client-Secret`.

---

### 3. Configuration Access Inconsistency & Potential `KeyError` in `tanyart_llm_service.py` - Severity: Major
* **Reviewer Lens:** `egm-codebase-details`
* **Affected Scope:** `docs/designs/migrasi_llm_ollama.md#L278-L286` (Section: `backend/services/tanyart_llm_service.py`)
* **Discrepancy Description**: In `backend/services/ai_fill_service.py` (lines 184–187), Cloudflare tokens are read defensively from `Config` (`getattr(Config, 'CF_CLIENT_ID', None)`). However, in `backend/services/tanyart_llm_service.py` (lines 69–70), `_chat()` directly accesses `os.environ["CF_CLIENT_ID"]` and `os.environ["CF_CLIENT_SECRET"]` via dictionary subscription. If campus routing is triggered when these environment variables are absent from `os.environ` or loaded only through `Config`, `_chat()` crashes with an unhandled `KeyError`. The implementation plan fails to specify aligning this access pattern.
* **Rationale & Recommendation**: Update the plan for File 5 (`tanyart_llm_service.py`) to explicitly instruct replacing `os.environ["CF_CLIENT_ID"]` with `getattr(Config, 'CF_CLIENT_ID', None)` or `os.environ.get()` with safe presence checks before initiating HTTPS connections to `ollama.ebruar.my.id`.

---

### 4. Ambiguity between Existing Codebase Baseline and New Delta Tasks - Severity: Major
* **Reviewer Lens:** `egm-codebase-details`
* **Affected Scope:** `docs/designs/migrasi_llm_ollama.md#L259-L286` (Sections: `config.py`, `ai_fill_service.py`, `tanyart_llm_service.py`)
* **Discrepancy Description**: Several proposed changes in the plan describe logic that is already implemented in the repository:
  - `config.py`: `LLM_MODEL = os.getenv('LLM_MODEL', 'qwen2.5:3b-instruct')`, `TANYART_LLM_BASE_URL` fallback, and `CF_CLIENT_ID`/`CF_CLIENT_SECRET` parsing are already present in lines 91–100.
  - `ai_fill_service.py`: URL `/v1` normalization and Cloudflare header injection are already present in lines 168–187.
  - `tanyart_llm_service.py`: `192.168.88.237` whitelist and `LLM_BASE_URL` fallback are already present in lines 43–48.
Listing already completed items under "Proposed Changes" without clear distinction confuses developers and AI implementers regarding what new code must actually be authored.
* **Rationale & Recommendation**: Explicitly split the plan into **Baseline Verified (No Changes Needed)** and **Actionable Delta Tasks**. Highlight the actual required changes (e.g., in `ai_fill_service.py`, strictly isolating `google.genai` imports and disabling `_call_gemini_api` runtime execution).

---

### 5. Inconsistent Timeout Budget vs. Total SLA (`TANYART_LLM_TIMEOUT`) - Severity: Major
* **Reviewer Lens:** `egm-style` / `egm-codebase-details`
* **Affected Scope:** `docs/designs/migrasi_llm_ollama.md#L247` and `L284`
* **Discrepancy Description**: The plan specifies `TANYART_LLM_TIMEOUT=5.0` in File 1 (`backend/.env`), but in File 5 and NFR 5.1 (line 221) mandates that "Budget pemanggilan inferensi Ollama dibatasi ketat maksimal 4.5 detik". In `tanyart_llm_service.py` (line 124), `budget` directly adopts `Config.TANYART_LLM_TIMEOUT`. If `.env` sets `5.0`, the inference budget alone can consume 5.0 seconds, which when added to lexical retrieval and processing time will violate the strict 5.0s total SLA.
* **Rationale & Recommendation**: Align the timeout specifications. In `backend/.env` and `backend/.env.example`, explicitly specify `TANYART_LLM_TIMEOUT=4.5` so that the inferencing budget leaves an intentional 500 ms buffer for end-to-end pipeline processing within the 5.0s SLA.

---

### 6. Under-specified Directives for `.env` and `.env.example` (Zero-Decision Rule Violation) - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness` / `egm-style`
* **Affected Scope:** `docs/designs/migrasi_llm_ollama.md#L248` and `L251-L258`
* **Discrepancy Description**:
  1. Line 248 instructs "Mengosongkan atau menghapus `GEMINI_API_KEY` dan `OPENAI_API_KEY`". This leaves an unapproved choice to the implementer (empty string assignment vs. key deletion). In Python dotenv, an empty string `KEY=` overrides host environment variables, whereas key deletion falls back to OS-level environment variables.
  2. Lines 254–256 describe additions to `backend/.env.example` in generic prose without providing the exact lines, comments, and placeholder values.
* **Rationale & Recommendation**: Uphold the Zero-Decision Rule by specifying the exact, literal entries:
  - Instruct setting `GEMINI_API_KEY=` and `OPENAI_API_KEY=` as empty values.
  - Provide the exact snippet to be inserted into `backend/.env.example`.

---

### 7. Working Directory Inconsistency in Verification Plan Commands - Severity: Nit
* **Reviewer Lens:** `egm-codebase-details`
* **Affected Scope:** `docs/designs/migrasi_llm_ollama.md#L306-L320` (Section: `Verification Plan`)
* **Discrepancy Description**: Test steps 1 and 2 instruct `cd backend && python ...`, whereas step 3 specifies `python -m py_compile backend/config.py backend/services/...`. If an engineer runs step 1 or 2 and remains in the `backend/` directory, step 3 will fail because `backend/config.py` does not exist relative to `backend/`.
* **Rationale & Recommendation**: Standardize all commands to execute consistently from the repository root (e.g. `python backend/test_tanyart_full.py`, `python backend/ukur_latensi_lengkap.py`, and `python -m py_compile backend/config.py ...`).

---

### 8. Coupling of Documentation Artifact in Target Code Files List - Severity: Nit
* **Reviewer Lens:** `egm-style` / `egm-implementation-readiness`
* **Affected Scope:** `docs/designs/migrasi_llm_ollama.md#L294-L298` (Target File 7: `concepts_brief.md`)
* **Discrepancy Description**: `concepts_brief.md` is an ideation brainstorming predecessor document. Listing it under `Target Files to Create/Modify` alongside backend runtime files blurs the boundary between codebase deliverables and documentation history, complicating automated change allowlists.
* **Rationale & Recommendation**: Separate codebase file modifications from documentation provenance updates by moving `concepts_brief.md` into a separate "Documentation & Provenance Updates" section or Phase 4.
