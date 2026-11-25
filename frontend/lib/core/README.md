# Core Subsystem

## Overview
The `core` layer provides foundational, domain-agnostic infrastructure, configurations, and services for the RTConnect Flutter client. It establishes application-wide constants, exception abstractions, centralized networking with secure token management, declarative routing with authentication guards, push notification lifecycle services, and design system tokens.

## Subdirectories & Boundaries
- [Constants](./constants/README.md): App-wide configuration, environment constants, dynamic base URL resolution, and secure storage keys
- [Errors](./errors/README.md): Custom domain exception handling, error classification, and localized user message models
- [Network](./network/README.md): Dio HTTP client, authorization interceptor, token persistence, and REST API endpoint paths
- [Router](./router/README.md): GoRouter declarative routing, authentication guards, persistent navigation shell, and sub-screen navigation
- [Services](./services/README.md): Firebase Cloud Messaging push notification lifecycle, token synchronization, and local notification handling
- [Theme](./theme/README.md): Design tokens (colors, typography, spacing) and Material 3 ThemeData implementation
