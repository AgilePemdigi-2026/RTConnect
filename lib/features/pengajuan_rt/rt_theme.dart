import 'package:flutter/material.dart';

import 'models/pengajuan.dart';

/// Warna mengikuti mockup Figma RTConnect.
class RtColors {
  static const primary = Color(0xFF0B57D0);
  static const navy = Color(0xFF0F1B2D);
  static const success = Color(0xFF0E9F6E);
  static const danger = Color(0xFFC62828);
  static const warning = Color(0xFFE69500);
  static const bg = Color(0xFFF4F5F9);
  static const card = Colors.white;
  static const muted = Color(0xFF6B7280);
  static const field = Color(0xFFF1F2F6);
}

class StatusStyle {
  final Color fg;
  final Color bg;
  final Color accent; // garis kiri kartu
  const StatusStyle(this.fg, this.bg, this.accent);

  static StatusStyle of(StatusPengajuan s) {
    switch (s) {
      case StatusPengajuan.diajukan:
        return const StatusStyle(RtColors.primary, Color(0xFFE3ECFD), RtColors.primary);
      case StatusPengajuan.perluRevisi:
        return const StatusStyle(RtColors.danger, Color(0xFFFDE7E7), RtColors.danger);
      case StatusPengajuan.ditolak:
        return const StatusStyle(Color(0xFF7F1D1D), Color(0xFFF3E1E1), Color(0xFF7F1D1D));
      case StatusPengajuan.disetujui:
      case StatusPengajuan.siapDiambil:
        return const StatusStyle(RtColors.warning, Color(0xFFFFF3DC), RtColors.warning);
      case StatusPengajuan.diambil:
      case StatusPengajuan.selesai:
        return const StatusStyle(RtColors.success, Color(0xFFDDF5EA), RtColors.success);
    }
  }
}

const _bulan = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'];
const _bulanPanjang = [
  'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
];

String _dua(int n) => n.toString().padLeft(2, '0');

/// 17 Agu 2026 • 09.42 WIB
String formatTanggalSingkat(DateTime d) =>
    '${d.day} ${_bulan[d.month - 1]} ${d.year} • ${_dua(d.hour)}.${_dua(d.minute)} WIB';

/// 17 Agustus 2026 / 09.42 WIB
String formatTanggalPanjang(DateTime d) =>
    '${d.day} ${_bulanPanjang[d.month - 1]} ${d.year} / ${_dua(d.hour)}.${_dua(d.minute)} WIB';

class StatusChip extends StatelessWidget {
  final StatusPengajuan status;
  const StatusChip(this.status, {super.key});

  @override
  Widget build(BuildContext context) {
    final s = StatusStyle.of(status);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(color: s.bg, borderRadius: BorderRadius.circular(20)),
      child: Text(status.label,
          style: TextStyle(color: s.fg, fontSize: 11, fontWeight: FontWeight.w600)),
    );
  }
}

class MetodeChip extends StatelessWidget {
  final MetodeTtd metode;
  const MetodeChip(this.metode, {super.key});

  @override
  Widget build(BuildContext context) {
    final digital = metode == MetodeTtd.digital;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: digital ? const Color(0xFFE3ECFD) : const Color(0xFFE5E7EB),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(digital ? 'TTD Digital (QR)' : 'TTD Basah (Cetak)',
          style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: digital ? RtColors.primary : const Color(0xFF374151))),
    );
  }
}
