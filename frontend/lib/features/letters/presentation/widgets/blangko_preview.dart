import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Identitas RT pada kop & tanda tangan surat.
/// SAMAKAN dengan backend/.env (RT_NUMBER, RW_NUMBER, RT_KELURAHAN, dst.).
class SuratIdentitas {
  static const String rt = '04';
  static const String rw = '09';
  static const String kelurahan = 'KEDURUS';
  static const String kotaTtd = 'Surabaya';
  static const String ketuaRt = 'Ahmad Dhafin';
  static const String ketuaRw = 'Alfarisy';
}

/// Pratinjau Surat Pengantar / Keterangan RT, meniru blangko resmi
/// (tata letak sama dengan PDF di backend/services/pdf_service.py).
class BlangkoPreview extends StatelessWidget {
  final String nama;
  final String alamat;
  final String pekerjaan;
  final String jenisKelamin;
  final String tempatTglLahir;
  final String agama;
  final String statusKawin;
  final String kewarganegaraan;
  final String kkKtp;
  final String tujuan;
  final String keperluan;
  final String keteranganLain;

  const BlangkoPreview({
    super.key,
    required this.nama,
    required this.alamat,
    required this.pekerjaan,
    required this.jenisKelamin,
    required this.tempatTglLahir,
    required this.agama,
    required this.statusKawin,
    required this.kewarganegaraan,
    required this.kkKtp,
    required this.tujuan,
    required this.keperluan,
    required this.keteranganLain,
  });

  @override
  Widget build(BuildContext context) {
    final body = GoogleFonts.tinos(fontSize: 9.5, height: 1.35, color: const Color(0xFF111111));
    final bold = body.copyWith(fontWeight: FontWeight.w700);

    final rows = <(String, String)>[
      ('Nama Lengkap', nama),
      ('A l a m a t', alamat),
      ('Pekerjaan', pekerjaan),
      ('Jenis Kelamin', jenisKelamin),
      ('Tempat / tgl. lahir', tempatTglLahir),
      ('A g a m a', agama),
      ('Kawin / tidak kawin', statusKawin),
      ('Kewarganegaraan', kewarganegaraan),
      ('Nomor KK / KTP', kkKtp),
      ('T u j u a n', tujuan),
      ('K e p e r l u a n', keperluan),
      ('', ''), // baris titik-titik kedua untuk keperluan (seperti blangko)
      ('Keterangan lain-lain', keteranganLain),
    ];

    Widget signature(List<String> top, String name) => Column(
          children: [
            for (final t in top) Text(t, style: body, textAlign: TextAlign.center),
            const SizedBox(height: 28),
            Text('( $name )', style: body, textAlign: TextAlign.center),
          ],
        );

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFE2E8F0),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Container(
        padding: const EdgeInsets.fromLTRB(20, 20, 18, 18),
        decoration: BoxDecoration(
          color: Colors.white,
          boxShadow: [
            BoxShadow(color: const Color(0xFF0F172A).withValues(alpha: 0.12), blurRadius: 3, offset: const Offset(0, 1)),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              Text('RT : ${SuratIdentitas.rt}', style: bold.copyWith(fontSize: 10.5)),
              const SizedBox(width: 56),
              Text('RW : ${SuratIdentitas.rw}', style: bold.copyWith(fontSize: 10.5)),
            ]),
            Text(
              'KELURAHAN : ${SuratIdentitas.kelurahan}',
              style: bold.copyWith(fontSize: 10.5, decoration: TextDecoration.underline),
            ),
            const SizedBox(height: 12),
            Center(
              child: Text(
                'SURAT PENGANTAR / KETERANGAN',
                style: bold.copyWith(fontSize: 12.5, decoration: TextDecoration.underline),
              ),
            ),
            Center(child: Text('No. ………………………', style: bold.copyWith(fontSize: 10.5))),
            const SizedBox(height: 8),
            Text('   Yang bertanda tangan di bawah ini, menerangkan :', style: body),
            const SizedBox(height: 2),
            for (final (label, value) in rows)
              Padding(
                padding: const EdgeInsets.only(top: 3),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    const SizedBox(width: 14),
                    SizedBox(width: 96, child: Text(label, style: body)),
                    SizedBox(width: 10, child: Text(label.isEmpty ? '' : ':', style: body)),
                    Expanded(
                      child: CustomPaint(
                        painter: const _DottedUnderline(),
                        child: Container(
                          constraints: const BoxConstraints(minHeight: 13),
                          padding: const EdgeInsets.only(bottom: 1.5),
                          child: Text(value, style: body),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            const SizedBox(height: 6),
            Padding(
              padding: const EdgeInsets.only(left: 14),
              child: Text('Demikian agar mendapat bantuan seperlunya', style: body),
            ),
            const SizedBox(height: 10),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(child: signature(['Tanda tangan', 'Yang bersangkutan'], nama)),
                Expanded(
                  child: signature(
                    ['${SuratIdentitas.kotaTtd}, ……………', 'Ketua RT. ${SuratIdentitas.rt}'],
                    SuratIdentitas.ketuaRt,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Center(child: Text('No. ………………………………', style: body)),
            const SizedBox(height: 6),
            Center(child: signature(['Mengetahui :', 'Ketua RW. ${SuratIdentitas.rw}'], SuratIdentitas.ketuaRw)),
          ],
        ),
      ),
    );
  }
}

/// Garis titik-titik di bawah isian, seperti blangko cetak.
class _DottedUnderline extends CustomPainter {
  const _DottedUnderline();

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0xFF111111)
      ..strokeWidth = 0.7;
    final y = size.height - 0.5;
    for (double x = 0; x < size.width; x += 2.6) {
      canvas.drawLine(Offset(x, y), Offset(x + 1, y), paint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
