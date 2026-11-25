# Chatbot Data

## Overview
Handles data communication between the RTConnect client and the Tanya RT lexical RAG / chatbot backend service.

## Interface
- `ChatbotRepository`:
  - `sendQuery({required String query, int? sessionId})`: Sends a resident question to the AI assistant endpoint and retrieves answer, citations, similarity scores, and escalation details.
  - `getSessions()`: Retrieves chat conversation history sessions for the authenticated user.
  - `getSessionMessages(int sessionId)`: Retrieves historical message threads for a specific chat session.

## Invariants
- `sendQuery` includes `session_id` in the request payload only when a non-null ID is provided.
- Returned JSON payloads are mapped into standard Dart `Map<String, dynamic>` maps.

## Side Effects
- Makes HTTP POST requests to `/api/v1/chatbot/query`.
- Makes HTTP GET requests to `/api/v1/chatbot/sessions` and `/api/v1/chatbot/sessions/<id>/messages`.

## Verification
- Run: `cd frontend && flutter test`
