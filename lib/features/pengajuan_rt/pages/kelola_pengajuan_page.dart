import 'package:flutter/material.dart';

import '../models/pengajuan.dart';
import '../rt_theme.dart';
import '../services/pengajuan_rt_service.dart';
import 'detail_pengajuan_page.dart';

enum _Filter { semua, diajukan, revisi, selesai }

/// Halaman "Pengajuan Warga" untuk Ketua RT (Gambar 1.6).
class KelolaPengajuanPage extends StatefulWidget {
  final PengajuanRtService service;
  const KelolaPengajuanPage({super.key, required this.service});

  @override
  State<KelolaPengajuanPage> createState() => _KelolaPengajuanPageState();
}

class _KelolaPengajuanPageState extends State<KelolaPengajuanPage> {
  List<Pengajuan> _semua = [];
  bool _loading = true;
  String? _error;
  String _cari = '';
  _Filter _filter = _Filter.semua;
  bool _terbaru = true;

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
      final data = await widget.service.daftarPengajuan();
      if (!mounted) return;
      setState(() {
        _semua = data;
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

  bool _isSelesai(Pengajuan p) =>
      p.status == StatusPengajuan.selesai || p.status == StatusPengajuan.diambil;

  int get _jmlDiajukan => _semua.where((p) => p.status == StatusPengajuan.diajukan).length;
  int get _jmlRevisi => _semua.where((p) => p.status == StatusPengajuan.perluRevisi).length;
  int get _jmlSelesai => _semua.where(_isSelesai).length;

  List<Pengajuan> get _tampil {
    final q = _cari.toLowerCase();
    final l = _semua.where((p) {
      final cocokFilter = switch (_filter) {
        _Filter.semua => true,
        _Filter.diajukan => p.status == StatusPengajuan.diajukan,
        _Filter.revisi => p.status == StatusPengajuan.perluRevisi,
        _Filter.selesai => _isSelesai(p),
      };
      final cocokCari = q.isEmpty ||
          p.namaWarga.toLowerCase().contains(q) ||
          p.jenisSurat.toLowerCase().contains(q) ||
          p.nomorPengajuan.toLowerCase().contains(q);
      return cocokFilter && cocokCari;
    }).toList();
    l.sort((a, b) => _terbaru
        ? b.tanggalPengajuan.compareTo(a.tanggalPengajuan)
        : a.tanggalPengajuan.compareTo(b.tanggalPengajuan));
    return l;
  }

  Future<void> _bukaDetail(Pengajuan p) async {
    final berubah = await Navigator.of(context).push<bool>(MaterialPageRoute(
      builder: (_) => DetailPengajuanPage(service: widget.service, pengajuanId: p.id),
    ));
    if (berubah == true) _muat();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: RtColors.bg,
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _muat,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
            children: [
              const Text('Pengajuan Warga',
                  style: TextStyle(fontSize: 26, fontWeight: FontWeight.w800, color: RtColors.navy)),
              const SizedBox(height: 4),
              const Text('Tinjau dan tindak lanjuti permohonan administrasi warga.',
                  style: TextStyle(color: RtColors.muted)),
              const SizedBox(height: 16),
              _ringkasan(),
              const SizedBox(height: 16),
              _kolomCari(),
              const SizedBox(height: 12),
              _barisFilter(),
              const SizedBox(height: 18),
              Row(children: [
                const Text('Daftar Permohonan',
                    style: TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                      color: const Color(0xFFE3ECFD), borderRadius: BorderRadius.circular(10)),
                  child: Text('${_tampil.length} Masuk',
                      style: const TextStyle(
                          color: RtColors.primary, fontSize: 11, fontWeight: FontWeight.w600)),
                ),
              ]),
              const SizedBox(height: 12),
              ..._isiDaftar(),
            ],
          ),
        ),
      ),
    );
  }

  List<Widget> _isiDaftar() {
    if (_loading) {
      return const [
        Padding(padding: EdgeInsets.all(40), child: Center(child: CircularProgressIndicator()))
      ];
    }
    if (_error != null) {
      return [
        _pesanKosong(Icons.cloud_off, 'Gagal memuat data', _error!),
        Center(child: TextButton(onPressed: _muat, child: const Text('Coba lagi'))),
      ];
    }
    final data = _tampil;
    if (data.isEmpty) {
      return [_pesanKosong(Icons.inbox_outlined, 'Tidak ada pengajuan', 'Coba ubah filter atau kata kunci.')];
    }
    return data
        .map((p) => Padding(
              padding: const EdgeInsets.only(bottom: 14),
              child: _KartuPengajuan(p, onTinjau: () => _bukaDetail(p)),
            ))
        .toList();
  }

  Widget _pesanKosong(IconData icon, String judul, String sub) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 40),
        child: Column(children: [
          Icon(icon, size: 48, color: RtColors.muted),
          const SizedBox(height: 8),
          Text(judul, style: const TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 4),
          Text(sub, textAlign: TextAlign.center, style: const TextStyle(color: RtColors.muted)),
        ]),
      );

  Widget _ringkasan() {
    Widget kotak(String label, int n, Color warna, IconData icon, {Color? bg}) => Expanded(
          child: Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
                color: bg ?? const Color(0xFFE9EAEE), borderRadius: BorderRadius.circular(14)),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                Text(label, style: TextStyle(fontSize: 12, color: warna == RtColors.danger ? warna : RtColors.muted)),
                const Spacer(),
                Container(width: 7, height: 7, decoration: BoxDecoration(color: warna, shape: BoxShape.circle)),
              ]),
              const SizedBox(height: 8),
              Row(children: [
                Text('$n',
                    style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.w800,
                        color: warna == RtColors.danger ? warna : RtColors.navy)),
                const Spacer(),
                Icon(icon, size: 18, color: warna),
              ]),
            ]),
          ),
        );
    return Row(children: [
      kotak('Diajukan', _jmlDiajukan, RtColors.primary, Icons.schedule),
      const SizedBox(width: 10),
      kotak('Revisi', _jmlRevisi, RtColors.danger, Icons.warning_amber_rounded,
          bg: const Color(0xFFFBEDED)),
      const SizedBox(width: 10),
      kotak('Selesai', _jmlSelesai, const Color(0xFF475569), Icons.check_circle_outline),
    ]);
  }

  Widget _kolomCari() => TextField(
        onChanged: (v) => setState(() => _cari = v),
        decoration: InputDecoration(
          hintText: 'Cari nama warga atau jenis surat...',
          prefixIcon: const Icon(Icons.search),
          filled: true,
          fillColor: Colors.white,
          contentPadding: const EdgeInsets.symmetric(vertical: 14),
          border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14), borderSide: BorderSide.none),
        ),
      );

  Widget _barisFilter() {
    Widget chip(_Filter f, String label, {int? jumlah, Color? dot}) {
      final aktif = _filter == f;
      return Padding(
        padding: const EdgeInsets.only(right: 8),
        child: ChoiceChip(
          selected: aktif,
          showCheckmark: false,
          onSelected: (_) => setState(() => _filter = f),
          selectedColor: RtColors.navy,
          backgroundColor: const Color(0xFFE9EAEE),
          side: BorderSide.none,
          shape: const StadiumBorder(),
          label: Row(mainAxisSize: MainAxisSize.min, children: [
            if (dot != null) ...[
              Container(width: 7, height: 7, decoration: BoxDecoration(color: dot, shape: BoxShape.circle)),
              const SizedBox(width: 6),
            ],
            Text(label,
                style: TextStyle(
                    color: aktif ? Colors.white : RtColors.navy,
                    fontSize: 12.5,
                    fontWeight: FontWeight.w600)),
            if (jumlah != null) ...[
              const SizedBox(width: 6),
              Text('$jumlah',
                  style: TextStyle(color: aktif ? Colors.white70 : RtColors.muted, fontSize: 12)),
            ],
          ]),
        ),
      );
    }

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(children: [
        chip(_Filter.semua, 'Semua', jumlah: _semua.length),
        chip(_Filter.diajukan, 'Diajukan', jumlah: _jmlDiajukan, dot: RtColors.primary),
        chip(_Filter.revisi, 'Revisi', jumlah: _jmlRevisi, dot: RtColors.danger),
        chip(_Filter.selesai, 'Selesai', jumlah: _jmlSelesai, dot: RtColors.success),
        ActionChip(
          onPressed: () => setState(() => _terbaru = !_terbaru),
          backgroundColor: Colors.white,
          side: const BorderSide(color: Color(0xFFE2E4EA)),
          shape: const StadiumBorder(),
          avatar: const Icon(Icons.swap_vert, size: 16),
          label: Text(_terbaru ? 'Terbaru' : 'Terlama', style: const TextStyle(fontSize: 12.5)),
        ),
      ]),
    );
  }
}

class _KartuPengajuan extends StatelessWidget {
  final Pengajuan p;
  final VoidCallback onTinjau;
  const _KartuPengajuan(this.p, {required this.onTinjau});

  IconData get _ikonSurat {
    final j = p.jenisSurat.toLowerCase();
    if (j.contains('usaha')) return Icons.storefront_outlined;
    if (j.contains('domisili')) return Icons.assignment_outlined;
    return Icons.description_outlined;
  }

  @override
  Widget build(BuildContext context) {
    final gaya = StatusStyle.of(p.status);
    final revisi = p.status == StatusPengajuan.perluRevisi;
    final selesai = p.status == StatusPengajuan.selesai || p.status == StatusPengajuan.diambil;

    return Container(
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        color: RtColors.card,
        borderRadius: BorderRadius.circular(16),
        boxShadow: const [BoxShadow(color: Color(0x0D000000), blurRadius: 8, offset: Offset(0, 2))],
      ),
      child: IntrinsicHeight(
        child: Row(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Container(width: 4, color: gaya.accent),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  CircleAvatar(
                    radius: 18,
                    backgroundColor: gaya.bg,
                    child: Text(p.inisial,
                        style: TextStyle(color: gaya.fg, fontWeight: FontWeight.w700, fontSize: 13)),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text(p.namaWarga,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15.5)),
                      Text('ID: ${p.nomorPengajuan}',
                          style: const TextStyle(fontSize: 11.5, color: RtColors.muted)),
                      Text(p.rtRw, style: const TextStyle(fontSize: 11.5, color: RtColors.muted)),
                    ]),
                  ),
                  StatusChip(p.status),
                ]),
                const SizedBox(height: 10),
                Row(children: [
                  Icon(_ikonSurat, size: 18, color: RtColors.navy),
                  const SizedBox(width: 6),
                  Text(p.jenisSurat, style: const TextStyle(fontWeight: FontWeight.w700)),
                ]),
                const SizedBox(height: 8),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(color: RtColors.field, borderRadius: BorderRadius.circular(10)),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text.rich(TextSpan(children: [
                      const TextSpan(text: 'Keperluan:  ', style: TextStyle(color: RtColors.muted, fontSize: 12)),
                      TextSpan(text: p.keperluan, style: const TextStyle(fontSize: 13)),
                    ])),
                    if (revisi && p.catatanRevisi != null) ...[
                      const SizedBox(height: 8),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                            color: const Color(0xFFFBEDED), borderRadius: BorderRadius.circular(8)),
                        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          const Icon(Icons.error_outline, size: 15, color: RtColors.danger),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text('Catatan RT: ${p.catatanRevisi}',
                                style: const TextStyle(
                                    color: RtColors.danger, fontSize: 12, fontWeight: FontWeight.w500)),
                          ),
                        ]),
                      ),
                    ],
                    const SizedBox(height: 8),
                    Row(children: [
                      const Icon(Icons.history, size: 14, color: RtColors.muted),
                      const SizedBox(width: 4),
                      Expanded(
                        child: Text(formatTanggalSingkat(p.tanggalPengajuan),
                            style: const TextStyle(fontSize: 11.5, color: RtColors.muted)),
                      ),
                      MetodeChip(p.metodeTtd),
                    ]),
                  ]),
                ),
                const SizedBox(height: 12),
                Row(children: [
                  Expanded(
                    child: SizedBox(
                      height: 44,
                      child: revisi
                          ? FilledButton.icon(
                              style: FilledButton.styleFrom(
                                backgroundColor: const Color(0xFFDDE1E6),
                                foregroundColor: RtColors.navy,
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                              ),
                              onPressed: onTinjau,
                              icon: const Icon(Icons.edit_note, size: 20),
                              label: const Text('Perbarui Catatan Revisi'),
                            )
                          : FilledButton.icon(
                              style: FilledButton.styleFrom(
                                backgroundColor: selesai ? RtColors.success : RtColors.primary,
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                              ),
                              onPressed: onTinjau,
                              icon: Icon(selesai ? Icons.draw_outlined : Icons.verified_outlined, size: 18),
                              label: const Text('Tinjau Pengajuan'),
                            ),
                    ),
                  ),
                  if (!revisi) ...[
                    const SizedBox(width: 8),
                    SizedBox(
                      width: 44,
                      height: 44,
                      child: IconButton.filledTonal(
                        style: IconButton.styleFrom(
                          backgroundColor: const Color(0xFFE5E7EB),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        onPressed: onTinjau,
                        icon: const Icon(Icons.visibility_outlined, color: RtColors.navy),
                      ),
                    ),
                  ],
                ]),
              ]),
            ),
          ),
        ]),
      ),
    );
  }
}
