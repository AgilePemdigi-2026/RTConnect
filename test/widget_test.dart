import 'package:flutter_test/flutter_test.dart';

import 'package:flutter_application_1/main.dart';

void main() {
  testWidgets('Halaman Pengajuan Warga tampil', (WidgetTester tester) async {
    await tester.pumpWidget(const RTConnectApp());
    expect(find.text('Pengajuan Warga'), findsOneWidget);

    // Tunggu data dummy selesai dimuat
    await tester.pumpAndSettle(const Duration(seconds: 1));
    expect(find.text('Ahmad Dhafin Al Farisy'), findsOneWidget);
  });
}
