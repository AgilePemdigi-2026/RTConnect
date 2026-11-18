import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rtconnect/features/chatbot/presentation/chatbot_screen.dart';

void main() {
  group('TEST-WGT-CHATBOT: ChatbotScreen', () {
    testWidgets('renders TanyaRT screen elements (Appbar, FAQ Chips, input field, send button)', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: ChatbotScreen(),
          ),
        ),
      );

      // Verify Title
      expect(find.text('TanyaRT'), findsOneWidget);
      expect(find.text('Asisten Pintar • Aktif 24 Jam'), findsOneWidget);

      // Verify FAQ Chips
      expect(find.text('Syarat Surat SKCK'), findsOneWidget);
      expect(find.text('Iuran RT Bulan Ini'), findsOneWidget);
      expect(find.text('Surat Domisili Usaha'), findsOneWidget);
      expect(find.text('Jadwal Kerja Bakti'), findsOneWidget);

      // Verify Initial Greeting Message
      expect(find.textContaining('Halo! Saya Tanya RT'), findsOneWidget);

      // Verify Input Field and Send Button
      expect(find.byType(TextField), findsOneWidget);
      expect(find.byIcon(Icons.send_rounded), findsOneWidget);
    });
  });
}
