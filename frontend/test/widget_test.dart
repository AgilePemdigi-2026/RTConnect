import 'package:flutter_test/flutter_test.dart';
import 'package:rtconnect/main.dart';

void main() {
  testWidgets('RTConnectApp inisialisasi dan menampilkan halaman pembuka', (WidgetTester tester) async {
    await tester.pumpWidget(const RTConnectApp());
    await tester.pump();

    // Pastikan teks aplikasi RTConnect berhasil dirender di Landing Page
    expect(find.text('RTConnect'), findsWidgets);
  });
}
