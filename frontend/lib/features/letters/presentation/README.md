# Letters Presentation

## Overview
Provides the complete user presentation workflow for letters in RTConnect, covering AI-assisted conversational application, manual multi-step form entry, document history tracking, detailed tracking, revision handling, PDF previewing, and RT officer verification/signing.

## Interface
- `letterRepositoryProvider`: Riverpod provider exposing `LetterRepository`.
- `letterTypesProvider`: FutureProvider supplying available letter types.
- `myApplicationsProvider`: FutureProvider listing user applications.
- `incomingQueueProvider`: FutureProvider listing RT incoming review applications.
- `applicationDetailProvider`: FutureProvider family querying application details by integer ID.
- `LetterSubmitState`: Immutable state tracking letter submission, approval, signing, and error states.
- `LetterSubmitController`: StateNotifier managing letter application submissions, review decisions, digital PIN signing, and physical confirmation.
- `letterSubmitControllerProvider`: Riverpod `StateNotifierProvider<LetterSubmitController, LetterSubmitState>`.
- `AIAssistantScreen`: Conversational form filling interface utilizing LLM parsing.
- `LetterApplicationScreen`: Multi-step form for citizen letter applications.
- `LetterDetailScreen`: Comprehensive detail view of application timeline, attachments, and status.
- `LetterHistoryScreen`: Historical log of all user letter submissions with filtering.
- `LetterRevisionScreen`: Form allowing citizens to edit and resubmit letters flagged with revision notes.
- `PdfViewerScreen`: In-app PDF viewer for generated official documents.
- `RTReviewScreen`: Review dashboard for RT officers to approve, reject, or request revisions.
- Subdirectories:
  - `widgets`: [./widgets/README.md](./widgets/README.md) - Specialized letter widgets (official blangko preview and PIN authorization dialog).

## Invariants
- Submitting decisions or signatures invalidates `incomingQueueProvider` and `applicationDetailProvider(id)` to trigger reactive UI refreshes.
- Submitting an application invalidates `myApplicationsProvider`.
- Server-side error messages from `AppException` are extracted and surfaced to the UI.

## Side Effects
- Mutates Riverpod state and triggers network refreshes.
- Reads device file attachments and renders PDFs via native viewer integrations.
- Modifies routing navigation stack via `go_router`.

## Verification
- Run: `cd frontend && flutter test`
