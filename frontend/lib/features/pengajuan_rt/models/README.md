# Pengajuan RT Models

## Overview
Defines data structures, status enumerations, and parsing logic for the standalone / legacy RT letter submission management demo subsystem.

## Interface
- `StatusPengajuan`: Enum representing submission stages (`diajukan`, `perluRevisi`, `ditolak`, `disetujui`, `siapDiambil`, `diambil`, `selesai`).
  - `fromString(String s)`: Factory mapping string labels to enum cases.
- `MetodeTtd`: Enum distinguishing signature methodology (`digital`, `basah`).
- `Pengajuan`: Immutable data model representing an RT submission entity, containing citizen identity, request purpose, attachment URLs, AI draft content, dues status (`iuranLunas`), and helper `inisial`.
  - `fromJson(Map<String, dynamic> j)`: JSON deserialization.
  - `copyWith(...)`: Copy mutation helper.

## Invariants
- `inisial` extracts up to two uppercase letters from the citizen's full name.
- Unknown status strings default to `StatusPengajuan.diajukan`.
- Dues status `iuranLunas` defaults to `false` if omitted from payload.

## Side Effects
- Pure data modeling and JSON parsing without external side effects.

## Verification
- Run: `cd frontend && flutter test`
