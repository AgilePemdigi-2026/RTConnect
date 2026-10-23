import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rtconnect/shared/widgets/rt_status_badge.dart';

void main() {
  group('TEST-WGT-002: RTStatusBadge', () {
    testWidgets('renders Perlu Revisi badge correctly', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: RTStatusBadge(status: 'perlu_revisi'),
          ),
        ),
      );

      expect(find.text('Perlu Revisi'), findsOneWidget);
    });

    testWidgets('renders Selesai badge correctly', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: RTStatusBadge(status: 'selesai'),
          ),
        ),
      );

      expect(find.text('Selesai'), findsOneWidget);
    });

    testWidgets('renders Diajukan badge correctly', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: RTStatusBadge(status: 'diajukan'),
          ),
        ),
      );

      expect(find.text('Diajukan'), findsOneWidget);
    });
  });
}
