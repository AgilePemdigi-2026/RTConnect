import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/errors/app_exception.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_typography.dart';
import '../../../shared/widgets/rt_primary_button.dart';
import 'letter_controller.dart';

/// Perbaikan surat yang diminta revisi oleh Ketua RT.
/// Warga dapat mengubah keperluan, tujuan, keterangan, DAN biodata pemohon
/// (atau mengisinya bila sebelumnya kosong), lalu mengirim ulang (PUT /letters/:id/resubmit).
class LetterRevisionScreen extends ConsumerStatefulWidget {
  final int applicationId;
  const LetterRevisionScreen({super.key, required this.applicationId});

  @override
  ConsumerState<LetterRevisionScreen> createState() => _LetterRevisionScreenState();
}

class _LetterRevisionScreenState extends ConsumerState<LetterRevisionScreen> {
  static const _jenisKelaminOptions = ['Laki-laki', 'Perempuan'];
  static const _agamaOptions = [
    'Islam', 'Kristen', 'Katolik', 'Hindu', 'Buddha', 'Konghucu',
    'Kepercayaan terhadap Tuhan YME',
  ];
  static const _statusKawinOptions = ['Belum Kawin', 'Kawin', 'Cerai Hidup', 'Cerai Mati'];
  static const _bulan = [
    'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember',
  ];

  final _formKey = GlobalKey<FormState>();
  final _keperluan = TextEditingController();
  final _tujuan = TextEditingController();
  final _keterangan = TextEditingController();
  final _pekerjaan = TextEditingController();
  final _tempatLahir = TextEditingController();
  final _kewarganegaraan = TextEditingController();
  final _nomorKk = TextEditingController();
  String? _jenisKelamin;
  String? _agama;
  String? _statusKawin;
  DateTime? _tanggalLahir;

  bool _prefilled = false;
  bool _sending = false;

  @override
  void dispose() {
    for (final c in [_keperluan, _tujuan, _keterangan, _pekerjaan, _tempatLahir, _kewarganegaraan, _nomorKk]) {
      c.dispose();
    }
    super.dispose();
  }

  void _prefill(Map<String, dynamic> d) {
    if (_prefilled) return;
    _prefilled = true;
    String t(String k) => d[k]?.toString() ?? '';
    String? opt(String k, List<String> o) => o.contains(d[k]) ? d[k] as String : null;
    _keperluan.text = t('keperluan');
    _tujuan.text = t('tujuan');
    _keterangan.text = t('keterangan_lain');
    _pekerjaan.text = t('pekerjaan');
    _tempatLahir.text = t('tempat_lahir');
    _kewarganegaraan.text = t('kewarganegaraan').isEmpty ? 'WNI' : t('kewarganegaraan');
    _nomorKk.text = t('nomor_kk');
    _jenisKelamin = opt('jenis_kelamin', _jenisKelaminOptions);
    _agama = opt('agama', _agamaOptions);
    _statusKawin = opt('status_kawin', _statusKawinOptions);
    _tanggalLahir = DateTime.tryParse(t('tanggal_lahir'));
  }

  String _iso(DateTime d) =>
      '${d.year}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  Future<void> _pilihTanggal() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _tanggalLahir ?? DateTime(now.year - 20),
      firstDate: DateTime(1900),
      lastDate: now.subtract(const Duration(days: 1)),
      helpText: 'Pilih tanggal lahir',
    );
    if (picked != null) setState(() => _tanggalLahir = picked);
  }

  Future<void> _kirim() async {
    final valid = _formKey.currentState?.validate() ?? false;
    if (!valid || _tanggalLahir == null) {
      setState(() {});
      _snack('Lengkapi dulu semua isian bertanda *.', error: true);
      return;
    }
    setState(() => _sending = true);
    try {
      await ref.read(letterRepositoryProvider).resubmitLetter(
        widget.applicationId,
        _keperluan.text.trim(),
        dataPemohon: {
          'pekerjaan': _pekerjaan.text.trim(),
          'jenis_kelamin': _jenisKelamin ?? '',
          'tempat_lahir': _tempatLahir.text.trim(),
          'tanggal_lahir': _iso(_tanggalLahir!),
          'agama': _agama ?? '',
          'status_kawin': _statusKawin ?? '',
          'kewarganegaraan': _kewarganegaraan.text.trim(),
          'nomor_kk': _nomorKk.text.trim(),
          'tujuan': _tujuan.text.trim(),
          'keterangan_lain': _keterangan.text.trim(),
        },
      );
      ref.invalidate(applicationDetailProvider(widget.applicationId));
      ref.invalidate(myApplicationsProvider);
      if (!mounted) return;
      _snack('Perbaikan terkirim. Surat diajukan ulang ke Ketua RT.');
      context.pop();
    } catch (e) {
      if (!mounted) return;
      final msg = (e is DioException && e.error is AppException)
          ? (e.error as AppException).message
          : 'Gagal mengirim perbaikan';
      _snack(msg, error: true);
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  void _snack(String msg, {bool error = false}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(backgroundColor: error ? AppColors.error : AppColors.success, content: Text(msg)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final detail = ref.watch(applicationDetailProvider(widget.applicationId));

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: Colors.white,
        surfaceTintColor: Colors.white,
        elevation: 0,
        title: Text('Perbaiki Pengajuan', style: AppTypography.titleSmall.copyWith(fontSize: 17)),
        bottom: const PreferredSize(
          preferredSize: Size.fromHeight(1),
          child: Divider(height: 1, color: AppColors.border),
        ),
      ),
      body: detail.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Gagal memuat pengajuan: $e')),
        data: (d) {
          _prefill(d);
          final catatan = d['catatan_revisi']?.toString();
          return SafeArea(
            top: false,
            child: Column(
              children: [
                Expanded(
                  child: Form(
                    key: _formKey,
                    // SingleChildScrollView (bukan ListView) agar SEMUA field ikut divalidasi.
                    child: SingleChildScrollView(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                        if (catatan != null && catatan.isNotEmpty) ...[
                          _catatanRt(catatan),
                          const SizedBox(height: 14),
                        ],
                        _card('Isian surat', [
                          _field('Keperluan *', _keperluan, maxLines: 3,
                              validator: (v) => (v == null || v.trim().length < 5) ? 'Keperluan wajib diisi' : null),
                          _field('Tujuan surat *', _tujuan, hint: 'Contoh: Polrestabes Surabaya'),
                          _field('Keterangan lain (opsional)', _keterangan, required: false, maxLines: 2),
                        ]),
                        const SizedBox(height: 14),
                        _card('Biodata pemohon', [
                          Text(
                            'Ubah bila ada yang salah, atau lengkapi bila sebelumnya kosong.',
                            style: AppTypography.caption.copyWith(color: AppColors.textMuted),
                          ),
                          const SizedBox(height: 12),
                          _field('Pekerjaan *', _pekerjaan, hint: 'Contoh: Karyawan Swasta'),
                          _dropdown('Jenis Kelamin *', _jenisKelamin, _jenisKelaminOptions,
                              (v) => setState(() => _jenisKelamin = v)),
                          _field('Tempat Lahir *', _tempatLahir, hint: 'Contoh: Surabaya'),
                          _tanggalField(),
                          _dropdown('Agama *', _agama, _agamaOptions, (v) => setState(() => _agama = v)),
                          _dropdown('Status Perkawinan *', _statusKawin, _statusKawinOptions,
                              (v) => setState(() => _statusKawin = v)),
                          _field('Kewarganegaraan *', _kewarganegaraan, hint: 'WNI'),
                          _field('Nomor Kartu Keluarga (KK) *', _nomorKk,
                              hint: '16 digit angka',
                              number: true,
                              validator: (v) => RegExp(r'^\d{16}$').hasMatch(v?.trim() ?? '')
                                  ? null
                                  : 'Nomor KK harus 16 digit angka'),
                        ]),
                        ],
                      ),
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
                  decoration: const BoxDecoration(
                    color: Colors.white,
                    border: Border(top: BorderSide(color: AppColors.border)),
                  ),
                  child: RTPrimaryButton(
                    text: 'Kirim Ulang ke Ketua RT',
                    icon: Icons.send_rounded,
                    isLoading: _sending,
                    onPressed: _sending ? null : _kirim,
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _catatanRt(String catatan) => Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: const Color(0xFFFFF7ED),
          border: Border.all(color: const Color(0xFFFED7AA)),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Catatan perbaikan dari Ketua RT',
                style: AppTypography.labelMedium.copyWith(color: const Color(0xFFC2410C), fontWeight: FontWeight.w700)),
            const SizedBox(height: 6),
            Text('"$catatan"',
                style: AppTypography.bodySmall.copyWith(color: const Color(0xFF7C2D12), fontStyle: FontStyle.italic)),
          ],
        ),
      );

  Widget _card(String title, List<Widget> children) => Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          border: Border.all(color: AppColors.border),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: AppTypography.labelLarge.copyWith(fontWeight: FontWeight.w700)),
            const SizedBox(height: 12),
            ...children,
          ],
        ),
      );

  InputDecoration _dekor(String hint) => InputDecoration(
        hintText: hint,
        isDense: true,
        counterText: '',
        filled: true,
        fillColor: Colors.white,
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.borderSubtle),
        ),
      );

  Widget _label(String text) => Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: Text(text, style: AppTypography.labelMedium.copyWith(color: AppColors.textSlate, fontSize: 12)),
      );

  Widget _field(String label, TextEditingController c,
          {String hint = '', bool required = true, int maxLines = 1, bool number = false,
          String? Function(String?)? validator}) =>
      Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _label(label),
            TextFormField(
              controller: c,
              minLines: 1,
              maxLines: maxLines,
              maxLength: number ? 16 : null,
              keyboardType: number ? TextInputType.number : null,
              inputFormatters: number ? [FilteringTextInputFormatter.digitsOnly] : null,
              validator: validator ??
                  (required
                      ? (v) => (v == null || v.trim().isEmpty) ? '${label.replaceAll(' *', '')} wajib diisi' : null
                      : null),
              decoration: _dekor(hint),
            ),
          ],
        ),
      );

  Widget _dropdown(String label, String? value, List<String> opts, ValueChanged<String?> onChanged) => Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _label(label),
            DropdownButtonFormField<String>(
              key: ValueKey('$label-$value'),
              initialValue: value,
              isExpanded: true,
              decoration: _dekor('Pilih'),
              items: [for (final o in opts) DropdownMenuItem(value: o, child: Text(o))],
              onChanged: onChanged,
              validator: (v) => v == null ? '${label.replaceAll(' *', '')} wajib dipilih' : null,
            ),
          ],
        ),
      );

  Widget _tanggalField() => Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _label('Tanggal Lahir *'),
            OutlinedButton.icon(
              onPressed: _pilihTanggal,
              icon: const Icon(Icons.calendar_today_outlined, size: 18),
              label: Align(
                alignment: Alignment.centerLeft,
                child: Text(_tanggalLahir == null
                    ? 'Pilih tanggal lahir'
                    : '${_tanggalLahir!.day} ${_bulan[_tanggalLahir!.month - 1]} ${_tanggalLahir!.year}'),
              ),
              style: OutlinedButton.styleFrom(
                minimumSize: const Size.fromHeight(46),
                foregroundColor: AppColors.textPrimary,
                side: BorderSide(color: _tanggalLahir == null ? AppColors.error : AppColors.borderSubtle),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
            if (_tanggalLahir == null)
              Padding(
                padding: const EdgeInsets.only(top: 4, left: 12),
                child: Text('Tanggal lahir wajib diisi',
                    style: AppTypography.caption.copyWith(color: AppColors.error)),
              ),
          ],
        ),
      );
}
