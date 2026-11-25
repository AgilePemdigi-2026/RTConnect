# Frontend (Flutter Client)

## Overview
Root directory of the RTConnect Flutter multi-platform client application. Houses package manifests (`pubspec.yaml`), platform host wrappers (Android, iOS, Web, macOS, Linux, Windows), and the complete client application architecture under `lib/`.

## Subdirectories & Boundaries
- [lib](./lib/README.md): Dart application source tree containing entrypoint `main.dart`, core infrastructure (`core/`), modular domain features (`features/`), and shared widgets (`shared/`).

## Verification
- Run: `cd frontend && flutter test`
