import 'package:flutter/material.dart';

import 'features/pengajuan_rt/pages/kelola_pengajuan_page.dart';
import 'features/pengajuan_rt/rt_theme.dart';
import 'features/pengajuan_rt/services/pengajuan_rt_service.dart';

void main() {
  runApp(const RTConnectApp());
}

class RTConnectApp extends StatelessWidget {
  const RTConnectApp({super.key});

  @override
  Widget build(BuildContext context) {
    // Sementara pakai data dummy (PIN: 482913).
    // Kalau backend Flask sudah jalan, ganti dengan:
    // ApiPengajuanRtService(baseUrl: 'http://10.0.2.2:5000/api', tokenProvider: () => token)
    final service = MockPengajuanRtService();

    return MaterialApp(
      title: 'RTConnect',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: RtColors.primary,
        scaffoldBackgroundColor: RtColors.bg,
      ),
      home: KelolaPengajuanPage(service: service),
    );
  }
}
