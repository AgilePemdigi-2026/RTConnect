# Chatbot Presentation

## Overview
Provides the conversational UI ("Tanya RT") and state management for resident inquiry answering, automated administrative guidance, and human RT escalation via WhatsApp.

## Interface
- `ChatMessage`: Model representing a conversational turn (sender `warga` or `bot`, text, citation, similarity score, escalation flag, WhatsApp link, timestamp).
- `ChatState`: State containing message history list, loading indicator, and current active session ID.
- `chatbotRepositoryProvider`: Riverpod provider exposing `ChatbotRepository`.
- `chatbotControllerProvider`: Riverpod `StateNotifierProvider<ChatbotController, ChatState>`.
- `ChatbotController`:
  - `sendMessage(String text)`: Appends user query, dispatches to backend, processes AI/RAG response or handles error fallbacks.
- `ChatbotScreen`: Interactive chat screen featuring quick-prompt chips, bubble list with legal citations, WhatsApp escalation action, and message composer.

## Invariants
- Initial state always seeds a welcome greeting from the Tanya RT bot configured for the active RT area.
- Empty or whitespace-only messages are discarded and not submitted to the backend.
- Existing session ID is tracked and reused for multi-turn conversation context unless updated by the backend.

## Side Effects
- Mutates conversational state in Riverpod.
- Launches external WhatsApp application via `url_launcher` when escalation link is tapped.
- Animates scrolling of the chat message list view.

## Verification
- Run: `cd frontend && flutter test`
