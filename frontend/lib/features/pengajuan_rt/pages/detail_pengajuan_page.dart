import 'package:flutter/material.dart';

import '../models/pengajuan.dart';
import '../rt_theme.dart';
import '../services/pengajuan_rt_service.dart';
import '../widgets/catatan_dialog.dart';
import '../widgets/pin_keamanan_dialog.dart';

/// Halaman "Detail Pengajuan" untuk Ketua RT (Gambar 1.7).
/// Pop dengan `true` kalau status pengajuan berubah, supaya daftar di-refresh.
class DetailPengajuanPage extends StatefulWidget {
  final PengajuanRtService service;
  final int pengajuanId;
  const DetailPengajuanPage({super.key, required this.service, required this.pengajuanId});

  @override
  State<DetailPengajuanPage> createState() => _DetailPengajuanPageState();
}

class _DetailPengajuanPageState extends State<DetailPengajuanPage> {
  Pengajuan? _p;
  bool _loading = true;
  bool _proses = false;
  bool _berubah = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _muat();
  }

  Future<void> _muat() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final p = await widget.service.detail(widget.pengajuanId);
      if (!mounted) return;
      setState(() {
        _p = p;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  void _snack(String pesan, {bool sukses = true}) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(pesan),
      behavior: SnackBarBehavior.floating,
      backgroundColor: sukses ? RtColors.success : RtColors.danger,
    ));
  }

  Future<void> _jalankan(Future<AksiResult> Function() aksi) async {
    setState(() => _proses = true);
    try {
      final r = await aksi();
      if (!mounted) return;
      _snack(r.pesan, sukses: r.sukses);
      if (r.sukses) {
        _berubah = true;
        await _muat();
      }
    } catch (e) {
      if (mounted) _snack('Terjadi kesalahan: $e', sukses: false);
    } finally {
      if (mounted) setState(() => _proses = false);
    }
  }

  // ---------- Aksi keputusan ----------

  Future<void> _setujui() async {
    final p = _p!;
    if (p.metodeTtd == MetodeTtd.basah) {
      final ok = await showDialog<bool>(
        context: context,
        builder: (c) => AlertDialog(
          title: const Text('Setujui & Cetak'),
          content: const Text(
              'Surat akan disiapkan untuk dicetak dan ditandatangani basah. Lanjutkan?'),
          actions: [
            TextButton(onPressed: () => Navigator.pop(c, false), child: const Text('Batal')),
            FilledButton(onPressed: () => Navigator.pop(c, true), child: const Text('Setujui')),
          ],
        ),
      );
      if (ok == true) await _jalankan(() => widget.service.setujuiBasah(p.id));
      return;
    }

    final hasil = await showPinKeamananDialog(
      context,
      onSubmit: (pin) => widget.service.sahkanDigital(p.id, pin),
    );
    if (hasil == null || !mounted) return;
    _berubah = true;
    await _muat();
    if (!mounted) return;
    await showDialog(
      context: context,
      builder: (c) => AlertDialog(
        icon: const Icon(Icons.verified, color: RtColors.success, size: 40),
        title: const Text('Surat Berhasil Disahkan'),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          Text(hasil.pesan, textAlign: TextAlign.center),
          if (hasil.nomorSurat != null) ...[
            const SizedBox(height: 12),
            const Text('Nomor Surat', style: TextStyle(color: RtColors.muted, fontSize: 12)),
            SelectableText(hasil.nomorSurat!,
                style: const TextStyle(fontWeight: FontWeight.w700, fontFamily: 'monospace')),
          ],
        ]),
        actions: [FilledButton(onPressed: () => Navigator.pop(c), child: const Text('Selesai'))],
      ),
    );
  }

  Future<void> _mintaRevisi() async {
    final catatan = await showCatatanSheet(
      context,
      judul: 'Minta Revisi',
      label: 'Catatan Revisi',
      hint: 'Contoh: KTP kurang jelas, mohon foto ulang',
      tombol: 'Kirim Catatan',
      warna: RtColors.warning,
      awal: _p!.catatanRevisi,
    );
    if (catatan != null) await _jalankan(() => widget.service.mintaRevisi(_p!.id, catatan));
  }

  Future<void> _tolak() async {
    final alasan = await showCatatanSheet(
      context,
      judul: 'Tolak Pengajuan',
      label: 'Alasan Penolakan',
      hint: 'Contoh: Bukan warga RT 04',
      tombol: 'Kirim Penolakan',
      warna: RtColors.danger,
    );
    if (alasan != null) await _jalankan(() => widget.service.tolak(_p!.id, alasan));
  }

  // ---------- UI ----------

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) Navigator.of(context).pop(_berubah);
      },
      child: Scaffold(
        backgroundColor: RtColors.bg,
        appBar: AppBar(
          backgroundColor: RtColors.bg,
          surfaceTintColor: Colors.transparent,
          leading: IconButton(
            style: IconButton.styleFrom(backgroundColor: const Color(0xFFE5E7EB)),
            icon: const Icon(Icons.arrow_back),
            onPressed: () => Navigator.of(context).pop(_berubah),
          ),
          centerTitle: true,
          title: Column(children: [
            const Text('Detail Pengajuan', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
            if (_p != null)
              Text('ID: ${_p!.nomorPengajuan}',
                  style: const TextStyle(fontSize: 11, color: RtColors.muted)),
          ]),
          actions: [
            if (_p != null) Padding(padding: const EdgeInsets.only(right: 12), child: StatusChip(_p!.status)),
          ],
        ),
        body: _isi(),
        bottomNavigationBar: _p == null ? null : _barAksi(),
      ),
    );
  }

  Widget _isi() {
    if (_loading && _p == null) return const Center(child: CircularProgressIndicator());
    if (_error != null && _p == null) {
      return Center(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Text(_error!, textAlign: TextAlign.center),
          TextButton(onPressed: _muat, child: const Text('Coba lagi')),
        ]),
      );
    }
    final p = _p!;
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
      children: [
        _kartu(
          child: Row(children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(color: RtColors.field, borderRadius: BorderRadius.circular(10)),
              child: const Icon(Icons.schedule, size: 20),
            ),
            const SizedBox(width: 12),
            Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('WAKTU DIAJUKAN', style: TextStyle(fontSize: 11, color: RtColors.muted)),
              Text(formatTanggalPanjang(p.tanggalPengajuan),
                  style: const TextStyle(fontWeight: FontWeight.w700)),
            ]),
          ]),
        ),
        if (p.status == StatusPengajuan.perluRevisi && p.catatanRevisi != null)
          _banner(Icons.edit_note, 'Catatan revisi terkirim', p.catatanRevisi!, RtColors.warning),
        if (p.status == StatusPengajuan.ditolak && p.alasanPenolakan != null)
          _banner(Icons.cancel_outlined, 'Pengajuan ditolak', p.alasanPenolakan!, RtColors.danger),
        _kartu(
          judul: 'IDENTITAS PEMOHON',
          trailing: p.iuranLunas
              ? const Row(mainAxisSize: MainAxisSize.min, children: [
                  Icon(Icons.check_circle, size: 14, color: RtColors.success),
                  SizedBox(width: 4),
                  Text('Warga Tetap', style: TextStyle(fontSize: 11, color: RtColors.success)),
                ])
              : null,
          child: Column(children: [
            Row(children: [
              CircleAvatar(
                radius: 22,
                backgroundColor: const Color(0xFFE3ECFD),
                child: Text(p.inisial,
                    style: const TextStyle(color: RtColors.primary, fontWeight: FontWeight.w700)),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(p.namaWarga, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
                  Text('NIK: ${p.nikSamaran}',
                      style: const TextStyle(fontFamily: 'monospace', fontSize: 12.5)),
                  const SizedBox(height: 2),
                  Row(children: [
                    const Icon(Icons.location_on_outlined, size: 14, color: RtColors.primary),
                    const SizedBox(width: 2),
                    Expanded(
                      child: Text(p.alamat,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontSize: 12, color: RtColors.muted)),
                    ),
                  ]),
                ]),
              ),
            ]),
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              decoration: BoxDecoration(color: RtColors.field, borderRadius: BorderRadius.circular(8)),
              child: Row(children: [
                Icon(Icons.receipt_long_outlined,
                    size: 16, color: p.iuranLunas ? RtColors.success : RtColors.warning),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(p.iuranLunas ? 'Iuran RT: Lunas' : 'Iuran RT: Belum lunas',
                      style: const TextStyle(fontSize: 12)),
                ),
              ]),
            ),
          ]),
        ),
        _kartu(
          judul: 'INFORMASI PERMOHONAN',
          child: Column(children: [
            Row(children: [
              Expanded(
                child: _infoKotak('Jenis Dokumen',
                    Row(children: [
                      const Icon(Icons.description_outlined, size: 16, color: RtColors.primary),
                      const SizedBox(width: 4),
                      Expanded(
                          child: Text(p.jenisSurat, style: const TextStyle(fontWeight: FontWeight.w700))),
                    ])),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _infoKotak(
                    'Metode Tandatangan',
                    Row(children: [
                      Icon(p.metodeTtd == MetodeTtd.digital ? Icons.qr_code_2 : Icons.draw_outlined,
                          size: 16, color: RtColors.primary),
                      const SizedBox(width: 4),
                      Text(p.metodeTtd == MetodeTtd.digital ? 'QR Digital' : 'TTD Basah',
                          style: const TextStyle(fontWeight: FontWeight.w700, color: RtColors.primary)),
                    ])),
              ),
            ]),
            const SizedBox(height: 10),
            _infoKotak(
              'Tujuan / Keperluan Administrasi',
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(p.keperluan, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
                if (p.deskripsiKeperluan != null) ...[
                  const SizedBox(height: 4),
                  Text(p.deskripsiKeperluan!, style: const TextStyle(fontSize: 12.5, color: RtColors.muted)),
                ],
              ]),
            ),
          ]),
        ),
        _kartu(
          judul: 'DOKUMEN PENDUKUNG',
          trailing: Text(p.lampiranNama == null ? 'Tidak ada' : '1 File Lampiran',
              style: const TextStyle(fontSize: 11, color: RtColors.muted)),
          child: p.lampiranNama == null
              ? const Text('Warga tidak melampirkan berkas.', style: TextStyle(color: RtColors.muted))
              : Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(color: RtColors.field, borderRadius: BorderRadius.circular(10)),
                  child: Row(children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                          color: const Color(0xFFFDE7E7), borderRadius: BorderRadius.circular(8)),
                      child: const Icon(Icons.picture_as_pdf_outlined, color: RtColors.danger),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text(p.lampiranNama!, style: const TextStyle(fontWeight: FontWeight.w600)),
                        Text('${p.lampiranUkuran ?? ''} • Diunggah Warga',
                            style: const TextStyle(fontSize: 11.5, color: RtColors.muted)),
                      ]),
                    ),
                    IconButton(
                        onPressed: () => _snack('Buka lampiran (sambungkan ke URL berkas)'),
                        icon: const Icon(Icons.visibility_outlined, size: 20)),
                    IconButton(
                        onPressed: () => _snack('Unduh lampiran (sambungkan ke URL berkas)'),
                        icon: const Icon(Icons.download_outlined, size: 20)),
                  ]),
                ),
        ),
        _kartu(
          judul: 'PRATINJAU DRAFT RESMI',
          trailing: TextButton.icon(
            style: TextButton.styleFrom(padding: EdgeInsets.zero, visualDensity: VisualDensity.compact),
            onPressed: () => _perbesarDraf(p),
            icon: const Icon(Icons.open_in_full, size: 14),
            label: const Text('Perbesar', style: TextStyle(fontSize: 12)),
          ),
          child: _DrafSurat(p),
        ),
      ],
    );
  }

  void _perbesarDraf(Pengajuan p) {
    showDialog(
      context: context,
      builder: (c) => Dialog(
        insetPadding: const EdgeInsets.all(12),
        child: Stack(children: [
          InteractiveViewer(
            maxScale: 4,
            child: SingleChildScrollView(padding: const EdgeInsets.all(16), child: _DrafSurat(p)),
          ),
          Positioned(
            right: 4,
            top: 4,
            child: IconButton(onPressed: () => Navigator.pop(c), icon: const Icon(Icons.close)),
          ),
        ]),
      ),
    );
  }

  Widget _barAksi() {
    final p = _p!;
    final bisaAksi = p.status == StatusPengajuan.diajukan || p.status == StatusPengajuan.perluRevisi;
    if (!bisaAksi) {
      return SafeArea(
        child: Container(
          margin: const EdgeInsets.all(12),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(14)),
          child: Row(children: [
            const Icon(Icons.info_outline, color: RtColors.muted),
            const SizedBox(width: 8),
            Expanded(child: Text('Pengajuan berstatus "${p.status.label}". Tidak ada tindakan lagi.')),
          ]),
        ),
      );
    }

    final digital = p.metodeTtd == MetodeTtd.digital;
    final revisi = p.status == StatusPengajuan.perluRevisi;

    return SafeArea(
      child: Container(
        margin: const EdgeInsets.fromLTRB(12, 0, 12, 12),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          boxShadow: const [BoxShadow(color: Color(0x14000000), blurRadius: 12, offset: Offset(0, -2))],
        ),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          if (!revisi)
            SizedBox(
              width: double.infinity,
              height: 50,
              child: FilledButton.icon(
                style: FilledButton.styleFrom(
                  backgroundColor: RtColors.success,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                onPressed: _proses ? null : _setujui,
                icon: _proses
                    ? const SizedBox(
                        width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : Icon(digital ? Icons.check_circle_outline : Icons.print_outlined),
                label: Text(digital ? 'Setujui & Tanda Tangani' : 'Setujui & Cetak (TTD Basah)',
                    style: const TextStyle(fontWeight: FontWeight.w600)),
              ),
            ),
          if (!revisi) const SizedBox(height: 8),
          Row(children: [
            Expanded(
              child: SizedBox(
                height: 44,
                child: TextButton.icon(
                  style: TextButton.styleFrom(
                    backgroundColor: const Color(0xFFFFF4DE),
                    foregroundColor: const Color(0xFFB45309),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  onPressed: _proses ? null : _mintaRevisi,
                  icon: const Icon(Icons.edit_note, size: 20),
                  label: Text(revisi ? 'Perbarui Catatan' : 'Minta Revisi'),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: SizedBox(
                height: 44,
                child: TextButton.icon(
                  style: TextButton.styleFrom(
                    backgroundColor: const Color(0xFFFDECEC),
                    foregroundColor: RtColors.danger,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  onPressed: _proses ? null : _tolak,
                  icon: const Icon(Icons.cancel_outlined, size: 18),
                  label: const Text('Tolak Pengajuan'),
                ),
              ),
            ),
          ]),
        ]),
      ),
    );
  }

  // ---------- helper widget ----------

  Widget _kartu({String? judul, Widget? trailing, required Widget child}) => Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(14)),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          if (judul != null) ...[
            Row(children: [
              Expanded(
                child: Text(judul,
                    style: const TextStyle(fontSize: 11, color: RtColors.muted, letterSpacing: 0.4)),
              ),
              if (trailing != null) trailing,
            ]),
            const SizedBox(height: 10),
          ],
          child,
        ]),
      );

  Widget _infoKotak(String label, Widget isi) => Container(
        width: double.infinity,
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(color: RtColors.field, borderRadius: BorderRadius.circular(10)),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(label, style: const TextStyle(fontSize: 11, color: RtColors.muted)),
          const SizedBox(height: 4),
          isi,
        ]),
      );

  Widget _banner(IconData icon, String judul, String isi, Color warna) => Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: warna.withOpacity(0.08),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: warna.withOpacity(0.3)),
        ),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Icon(icon, color: warna, size: 20),
          const SizedBox(width: 8),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(judul, style: TextStyle(fontWeight: FontWeight.w700, color: warna)),
              const SizedBox(height: 2),
              Text(isi, style: const TextStyle(fontSize: 13)),
            ]),
          ),
        ]),
      );
}

/// Pratinjau draf surat dengan kop (versi tampilan; PDF asli dibuat backend).
class _DrafSurat extends StatelessWidget {
  final Pengajuan p;
  const _DrafSurat(this.p);

  @override
  Widget build(BuildContext context) {
    const mono = TextStyle(fontFamily: 'monospace', fontSize: 11);
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFF8F9FB),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0xFFE2E4EA)),
      ),
      child: Column(children: [
        const Text('RUKUN TETANGGA 04 / RW 07',
            style: TextStyle(fontWeight: FontWeight.w800, fontSize: 14)),
        const Text('KELURAHAN TAWANGSARI • KECAMATAN TAMAN', style: TextStyle(fontSize: 10.5)),
        const Text('Sekretariat: Balai Warga RT 04, Jl. Kemuning Indah No. 01',
            textAlign: TextAlign.center, style: TextStyle(fontSize: 9.5, color: RtColors.muted)),
        const Divider(thickness: 2, color: RtColors.navy, height: 18),
        Text(p.jenisSurat.toUpperCase(),
            style: const TextStyle(
                fontWeight: FontWeight.w800, decoration: TextDecoration.underline, fontSize: 13)),
        const Text('Nomor: (diterbitkan setelah disetujui)', style: mono),
        const SizedBox(height: 10),
        Align(
          alignment: Alignment.centerLeft,
          child: Text(
            p.drafSurat ?? 'Draf surat belum tersedia.',
            style: const TextStyle(fontSize: 12, height: 1.4),
          ),
        ),
        const SizedBox(height: 14),
        Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
          const Expanded(
            child: Text('RTConnect Digital\nVerified', style: TextStyle(fontSize: 9.5, color: RtColors.muted)),
          ),
          Column(children: [
            Text('Tawangsari, ${formatTanggalSingkat(p.tanggalPengajuan).split(' •').first}',
                style: const TextStyle(fontSize: 10)),
            const Text('Ketua RT 04', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700)),
            const SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(color: const Color(0xFFFFF3C4), borderRadius: BorderRadius.circular(6)),
              child: Text(
                p.status == StatusPengajuan.selesai ? 'SUDAH DITANDATANGANI' : 'SIAP DITANDATANGANI',
                style: const TextStyle(fontSize: 9.5, fontWeight: FontWeight.w700, color: Color(0xFFB45309)),
              ),
            ),
            const SizedBox(height: 4),
            const Text('( Ketua RT )', style: TextStyle(fontSize: 10.5, fontWeight: FontWeight.w600)),
          ]),
        ]),
      ]),
    );
  }
}
