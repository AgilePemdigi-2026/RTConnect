import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rtconnect/shared/widgets/rt_primary_button.dart';

void main() {
  group('TEST-WGT-001: RTPrimaryButton', () {
    testWidgets('renders button text and triggers onPressed when not loading', (tester) async {
      bool pressed = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: RTPrimaryButton(
              text: 'Kirim Permohonan',
              onPressed: () => pressed = true,
            ),
          ),
        ),
      );

      expect(find.text('Kirim Permohonan'), findsOneWidget);
      expect(find.byType(CircularProgressIndicator), findsNothing);

      await tester.tap(find.byType(ElevatedButton));
      await tester.pump();

      expect(pressed, isTrue);
    });

    testWidgets('renders CircularProgressIndicator and disables tap when isLoading is true', (tester) async {
      bool pressed = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: RTPrimaryButton(
              text: 'Kirim Permohonan',
              isLoading: true,
              onPressed: () => pressed = true,
            ),
          ),
        ),
      );

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(find.text('Kirim Permohonan'), findsNothing);

      await tester.tap(find.byType(ElevatedButton));
      await tester.pump();

      expect(pressed, isFalse);
    });
  });
}
