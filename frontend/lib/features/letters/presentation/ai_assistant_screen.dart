import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/errors/app_exception.dart';
import '../../../core/router/route_names.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_typography.dart';
import '../../../shared/widgets/rt_primary_button.dart';
import '../../auth/presentation/auth_controller.dart';
import 'letter_controller.dart';
import 'widgets/blangko_preview.dart';

/// Pengajuan surat dengan Asisten AI:
/// 1. Asisten  -> warga bercerita, AI mengisi formulir (POST /letters/ai-fill)
/// 2. Hasil    -> cek isian; biodata tersimpan dipakai ulang, tujuan diisi baru
/// 3. Konfirmasi -> pratinjau blangko resmi, lalu ajukan (POST /letters/apply)
class AiAssistantScreen extends ConsumerStatefulWidget {
  const AiAssistantScreen({super.key});

  @override
  ConsumerState<AiAssistantScreen> createState() => _AiAssistantScreenState();
}

enum _Step { asisten, hasil, konfirmasi }

enum _Sumber { ai, tersimpan, bawaan, kosong }

class _ChatMessage {
  final bool fromUser;
  final String text;
  final bool isError;
  const _ChatMessage(this.text, {this.fromUser = false, this.isError = false});
}

// Warna label sumber isian
const _aiBg = Color(0xFFDBEAFE);
const _aiFg = Color(0xFF1D4ED8);
const _savedBg = Color(0xFFD1FAE5);
const _savedFg = Color(0xFF047857);
const _missingBg = Color(0xFFFEF3C7);
const _missingFg = Color(0xFF92400E);

class _AiAssistantScreenState extends ConsumerState<AiAssistantScreen> {
  static const _maxPesan = 600;
  static const _contohCepat = {
    'Pengantar SKCK': 'Saya mau bikin surat pengantar SKCK untuk ',
    'Keterangan domisili': 'Saya butuh surat keterangan domisili untuk ',
    'Pengantar KTP/KK': 'Saya mau mengurus KTP/KK, perlu surat pengantar untuk ',
    'Keterangan usaha': 'Saya butuh surat keterangan usaha untuk ',
  };
  static const _jenisKelaminOptions = ['Laki-laki', 'Perempuan'];
  static const _agamaOptions = [
    'Islam', 'Kristen', 'Katolik', 'Hindu', 'Buddha', 'Konghucu',
    'Kepercayaan terhadap Tuhan YME',
  ];
  static const _statusKawinOptions = ['Belum Kawin', 'Kawin', 'Cerai Hidup', 'Cerai Mati'];
  static const _biodataFields = [
    'pekerjaan', 'jenis_kelamin', 'tempat_lahir', 'tanggal_lahir',
    'agama', 'status_kawin', 'kewarganegaraan', 'nomor_kk',
  ];

  _Step _step = _Step.asisten;

  // Langkah 1: percakapan
  final _pesanController = TextEditingController();
  final _scrollController = ScrollController();
  final List<_ChatMessage> _messages = [
    const _ChatMessage(
      'Halo, Pak/Bu! Ceritakan saja surat apa yang dibutuhkan dan untuk apa. '
      'Biodata dari pengajuan sebelumnya otomatis dipakai lagi, jadi cukup sebutkan keperluan dan tujuannya.',
    ),
  ];
  bool _loadingAi = false;

  // Langkah 2: isian formulir
  final _formKey = GlobalKey<FormState>();
  final _keperluanController = TextEditingController();
  final _tujuanController = TextEditingController();
  final _keteranganController = TextEditingController();
  final _pekerjaanController = TextEditingController();
  final _tempatLahirController = TextEditingController();
  final _kewarganegaraanController = TextEditingController(text: 'WNI');
  final _nomorKkController = TextEditingController();
  int? _jenisSuratId;
  String? _jenisKelamin;
  String? _agama;
  String? _statusKawin;
  DateTime? _tanggalLahir;
  String _metodeTtd = 'digital';
  bool _jenisDariAi = false;
  bool _keperluanDariAi = false;
  Map<String, _Sumber> _sumber = {};
  bool _sudahDiisi = false;
  String? _pertanyaan;
  bool _editBiodata = false;

  // Langkah 3
  bool _setuju = false;

  @override
  void dispose() {
    for (final c in [
      _pesanController, _keperluanController, _tujuanController, _keteranganController,
      _pekerjaanController, _tempatLahirController, _kewarganegaraanController, _nomorKkController,
    ]) {
      c.dispose();
    }
    _scrollController.dispose();
    super.dispose();
  }

  // ---------------------------------------------------------------- logika

  Future<void> _kirimPesan() async {
    final pesan = _pesanController.text.trim();
    if (pesan.length < 5 || _loadingAi) {
      if (pesan.length < 5) _snack('Ceritakan sedikit lebih lengkap (minimal 5 karakter).');
      return;
    }
    FocusScope.of(context).unfocus();
    setState(() {
      _messages.add(_ChatMessage(pesan, fromUser: true));
      _loadingAi = true;
      _pesanController.clear();
    });
    _scrollToBottom();

    try {
      final result = await ref.read(letterRepositoryProvider).aiFill(pesan);
      if (!mounted) return;
      _terapkanHasil(result);
      final aiDipakai = result['ai_digunakan'] == true;
      setState(() {
        _loadingAi = false;
        _messages.add(_ChatMessage(aiDipakai
            ? 'Formulir sudah saya isi. Silakan periksa dulu sebelum diajukan.'
            : (result['pesan']?.toString() ??
                'Asisten AI sedang tidak tersedia. Formulir diisi dari data sebelumnya.')));
        _step = _Step.hasil;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _loadingAi = false;
        _messages.add(_ChatMessage(
          'Maaf, permintaan gagal: ${_pesanError(e)}. Coba kirim lagi atau isi formulir manual.',
          isError: true,
        ));
      });
    }
    _scrollToBottom();
  }

  void _terapkanHasil(Map<String, dynamic> r) {
    final data = Map<String, dynamic>.from((r['data_pemohon'] ?? {}) as Map);
    final sumberRaw = Map<String, dynamic>.from((r['sumber'] ?? {}) as Map);
    String text(String k) => data[k]?.toString() ?? '';
    String? option(String k, List<String> opts) => opts.contains(data[k]) ? data[k] as String : null;

    final jenis = r['jenis_surat'] == null ? null : Map<String, dynamic>.from(r['jenis_surat'] as Map);
    _jenisSuratId = jenis?['jenis_surat_id'] as int? ?? _jenisSuratId;
    _jenisDariAi = jenis != null;
    final keperluan = r['keperluan']?.toString() ?? '';
    if (keperluan.isNotEmpty) _keperluanController.text = keperluan;
    _keperluanDariAi = keperluan.isNotEmpty;
    final metode = r['metode_tanda_tangan']?.toString();
    if (metode == 'digital' || metode == 'basah') _metodeTtd = metode!;

    _pekerjaanController.text = text('pekerjaan');
    _tempatLahirController.text = text('tempat_lahir');
    _kewarganegaraanController.text = text('kewarganegaraan').isEmpty ? 'WNI' : text('kewarganegaraan');
    _nomorKkController.text = text('nomor_kk');
    _tujuanController.text = text('tujuan');
    _keteranganController.text = text('keterangan_lain');
    _jenisKelamin = option('jenis_kelamin', _jenisKelaminOptions);
    _agama = option('agama', _agamaOptions);
    _statusKawin = option('status_kawin', _statusKawinOptions);
    _tanggalLahir = DateTime.tryParse(text('tanggal_lahir'));

    // Hanya sumber yang diketahui; field kosong ditandai "Perlu diisi" saat ditampilkan,
    // field yang diketik sendiri oleh warga tidak diberi label.
    _sumber = {};
    for (final f in [..._biodataFields, 'tujuan', 'keterangan_lain']) {
      final s = switch (sumberRaw[f]) {
        'ai' => _Sumber.ai,
        'tersimpan' => _Sumber.tersimpan,
        'bawaan' => _Sumber.bawaan,
        _ => null,
      };
      if (s != null) _sumber[f] = s;
    }
    _sudahDiisi = true;
    _pertanyaan = r['pertanyaan']?.toString();
    // Biodata lengkap -> tampil ringkas; ada yang kosong -> langsung bisa diisi.
    _editBiodata = !_biodataLengkap;
    _setuju = false;
  }

  bool get _biodataLengkap =>
      _pekerjaanController.text.trim().isNotEmpty &&
      _jenisKelamin != null &&
      _tempatLahirController.text.trim().isNotEmpty &&
      _tanggalLahir != null &&
      _agama != null &&
      _statusKawin != null &&
      _kewarganegaraanController.text.trim().isNotEmpty &&
      RegExp(r'^\d{16}$').hasMatch(_nomorKkController.text.trim());

  List<String> get _kurang => [
        if (_jenisSuratId == null) 'jenis surat',
        if (_keperluanController.text.trim().isEmpty) 'keperluan',
        if (_tujuanController.text.trim().isEmpty) 'tujuan surat',
        if (!_biodataLengkap) 'biodata',
      ];

  void _lanjutKePratinjau() {
    final valid = _formKey.currentState?.validate() ?? false;
    if (!_biodataLengkap) setState(() => _editBiodata = true);
    if (!valid || _kurang.isNotEmpty) {
      _snack('Lengkapi dulu: ${_kurang.join(', ')}.');
      return;
    }
    setState(() {
      _step = _Step.konfirmasi;
      _setuju = false;
    });
  }

  Future<void> _ajukan() async {
    final ok = await ref.read(letterSubmitControllerProvider.notifier).submitApplication(
          jenisSuratId: _jenisSuratId!,
          keperluan: _keperluanController.text.trim(),
          metodeTandaTangan: _metodeTtd,
          dataPemohon: {
            'pekerjaan': _pekerjaanController.text.trim(),
            'jenis_kelamin': _jenisKelamin ?? '',
            'tempat_lahir': _tempatLahirController.text.trim(),
            'tanggal_lahir': _tanggalLahir == null ? '' : _isoTanggal(_tanggalLahir!),
            'agama': _agama ?? '',
            'status_kawin': _statusKawin ?? '',
            'kewarganegaraan': _kewarganegaraanController.text.trim(),
            'nomor_kk': _nomorKkController.text.trim(),
            'tujuan': _tujuanController.text.trim(),
            'keterangan_lain': _keteranganController.text.trim(),
          },
        );
    if (!mounted) return;
    if (ok) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        backgroundColor: AppColors.success,
        content: Text('Permohonan surat berhasil dikirim ke Ketua RT.'),
      ));
      context.go(RouteNames.wargaPengajuan);
    } else {
      _snack(ref.read(letterSubmitControllerProvider).errorMessage ?? 'Gagal mengirim permohonan');
    }
  }

  void _kembali() {
    switch (_step) {
      case _Step.konfirmasi:
        setState(() => _step = _Step.hasil);
      case _Step.hasil:
        setState(() => _step = _Step.asisten);
      case _Step.asisten:
        if (context.canPop()) {
          context.pop();
        } else {
          context.go(RouteNames.wargaHome);
        }
    }
  }

  Future<void> _pilihTanggalLahir() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _tanggalLahir ?? DateTime(now.year - 20),
      firstDate: DateTime(1900),
      lastDate: now.subtract(const Duration(days: 1)),
      helpText: 'Pilih tanggal lahir',
    );
    if (picked != null) {
      setState(() {
        _tanggalLahir = picked;
        _sumber.remove('tanggal_lahir');
      });
    }
  }

  String _pesanError(Object e) {
    if (e is DioException && e.error is AppException) return (e.error as AppException).message;
    if (e is DioException && e.type == DioExceptionType.receiveTimeout) return 'asisten terlalu lama menjawab';
    return 'koneksi ke server bermasalah';
  }

  void _snack(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(backgroundColor: AppColors.error, content: Text(msg)),
    );
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  static const _bulan = [
    'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember',
  ];
  String _isoTanggal(DateTime d) =>
      '${d.year}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
  String _tanggalPanjang(DateTime? d) => d == null ? '' : '${d.day} ${_bulan[d.month - 1]} ${d.year}';

  String _namaJenis(List<Map<String, dynamic>> types) {
    final t = types.where((e) => e['jenis_surat_id'] == _jenisSuratId);
    return t.isEmpty ? 'Pilih jenis surat' : t.first['nama_surat'].toString();
  }

  // ---------------------------------------------------------------- tampilan

  @override
  Widget build(BuildContext context) {
    final (judul, subjudul) = switch (_step) {
      _Step.asisten => ('Asisten Pengajuan', 'Ceritakan surat yang kamu butuhkan'),
      _Step.hasil => ('Hasil Isian AI', 'Periksa dulu sebelum diajukan'),
      _Step.konfirmasi => ('Konfirmasi Pengajuan', 'Langkah terakhir sebelum dikirim ke Ketua RT'),
    };

    return PopScope(
      canPop: _step == _Step.asisten,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) _kembali();
      },
      child: Scaffold(
        backgroundColor: AppColors.background,
        appBar: AppBar(
          backgroundColor: Colors.white,
          surfaceTintColor: Colors.white,
          elevation: 0,
          leading: IconButton(
            tooltip: 'Kembali',
            icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 20, color: AppColors.textPrimary),
            onPressed: _kembali,
          ),
          titleSpacing: 0,
          title: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(judul, style: AppTypography.titleSmall.copyWith(color: AppColors.textPrimary, fontSize: 17)),
              Text(subjudul, style: AppTypography.caption.copyWith(color: AppColors.textMuted)),
            ],
          ),
          actions: [
            if (_step == _Step.asisten)
              Container(
                margin: const EdgeInsets.only(right: 16),
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(color: _aiBg, borderRadius: BorderRadius.circular(999)),
                child: Row(children: [
                  const Icon(Icons.auto_awesome_rounded, size: 14, color: _aiFg),
                  const SizedBox(width: 4),
                  Text('AI', style: AppTypography.labelSmall.copyWith(color: _aiFg, fontWeight: FontWeight.w700)),
                ]),
              ),
          ],
          bottom: const PreferredSize(
            preferredSize: Size.fromHeight(1),
            child: Divider(height: 1, color: AppColors.border),
          ),
        ),
        body: SafeArea(
          top: false,
          child: switch (_step) {
            _Step.asisten => _buildAsisten(),
            _Step.hasil => _buildHasil(),
            _Step.konfirmasi => _buildKonfirmasi(),
          },
        ),
      ),
    );
  }

  // ---- Langkah 1: Asisten

  Widget _buildAsisten() {
    final sudahAdaHasil = _sudahDiisi;
    return Column(
      children: [
        Expanded(
          child: ListView(
            controller: _scrollController,
            padding: const EdgeInsets.fromLTRB(16, 20, 16, 16),
            children: [
              for (final (i, m) in _messages.indexed) ...[
                _bubble(m),
                if (i == 0 && _messages.length == 1) _quickChips(),
                const SizedBox(height: 14),
              ],
              if (_loadingAi) _typingBubble(),
              if (sudahAdaHasil && !_loadingAi)
                Align(
                  alignment: Alignment.centerLeft,
                  child: TextButton.icon(
                    onPressed: () => setState(() => _step = _Step.hasil),
                    icon: const Icon(Icons.arrow_forward_rounded, size: 18),
                    label: const Text('Lihat hasil isian terakhir'),
                  ),
                ),
              const SizedBox(height: 8),
              _privacyNote(),
            ],
          ),
        ),
        _inputBar(),
      ],
    );
  }

  Widget _avatar() => Container(
        width: 32,
        height: 32,
        decoration: BoxDecoration(color: AppColors.primaryBrand, borderRadius: BorderRadius.circular(10)),
        child: const Icon(Icons.auto_awesome_rounded, size: 18, color: Colors.white),
      );

  Widget _bubble(_ChatMessage m) {
    if (m.fromUser) {
      return Align(
        alignment: Alignment.centerRight,
        child: Container(
          constraints: const BoxConstraints(maxWidth: 290),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          decoration: const BoxDecoration(
            color: AppColors.primaryBrand,
            borderRadius: BorderRadius.only(
              topLeft: Radius.circular(16), topRight: Radius.circular(4),
              bottomLeft: Radius.circular(16), bottomRight: Radius.circular(16),
            ),
          ),
          child: Text(m.text, style: AppTypography.bodyMedium.copyWith(color: Colors.white, height: 1.5)),
        ),
      );
    }
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _avatar(),
        const SizedBox(width: 10),
        Flexible(
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            decoration: BoxDecoration(
              color: m.isError ? const Color(0xFFFEE2E2) : Colors.white,
              border: Border.all(color: m.isError ? const Color(0xFFFECACA) : AppColors.border),
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(4), topRight: Radius.circular(16),
                bottomLeft: Radius.circular(16), bottomRight: Radius.circular(16),
              ),
            ),
            child: Text(
              m.text,
              style: AppTypography.bodyMedium.copyWith(
                color: m.isError ? const Color(0xFF991B1B) : AppColors.textPrimary,
                height: 1.5,
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _quickChips() => Padding(
        padding: const EdgeInsets.only(left: 42, top: 14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Contoh cepat', style: AppTypography.labelSmall.copyWith(color: AppColors.textMuted)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final e in _contohCepat.entries)
                  ActionChip(
                    label: Text(e.key),
                    labelStyle: AppTypography.labelMedium.copyWith(color: AppColors.textSlate, fontSize: 13),
                    backgroundColor: Colors.white,
                    side: const BorderSide(color: AppColors.borderSubtle),
                    shape: const StadiumBorder(),
                    onPressed: () {
                      _pesanController.text = e.value;
                      _pesanController.selection =
                          TextSelection.collapsed(offset: _pesanController.text.length);
                      setState(() {});
                    },
                  ),
              ],
            ),
          ],
        ),
      );

  Widget _typingBubble() => Row(
        children: [
          _avatar(),
          const SizedBox(width: 10),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            decoration: BoxDecoration(
              color: Colors.white,
              border: Border.all(color: AppColors.border),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Row(children: [
              const SizedBox(
                width: 14, height: 14,
                child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.primaryLight),
              ),
              const SizedBox(width: 10),
              Text('Mengisi formulir untukmu…',
                  style: AppTypography.bodySmall.copyWith(color: AppColors.textSecondary)),
            ]),
          ),
        ],
      );

  Widget _privacyNote() => Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: AppColors.primaryBg,
          border: Border.all(color: AppColors.primaryContainer),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Icon(Icons.verified_user_outlined, size: 18, color: AppColors.primaryBrand),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                'NIK, No. KK, agama, dan nomor HP tidak dikirim ke AI. Data itu diisi langsung dari akunmu.',
                style: AppTypography.caption.copyWith(color: const Color(0xFF1E3A8A), height: 1.5),
              ),
            ),
          ],
        ),
      );

  Widget _inputBar() => Container(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
        decoration: const BoxDecoration(
          color: Colors.white,
          border: Border(top: BorderSide(color: AppColors.border)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Expanded(
                  child: TextField(
                    controller: _pesanController,
                    enabled: !_loadingAi,
                    minLines: 1,
                    maxLines: 4,
                    maxLength: _maxPesan,
                    maxLengthEnforcement: MaxLengthEnforcement.enforced,
                    textCapitalization: TextCapitalization.sentences,
                    onChanged: (_) => setState(() {}),
                    decoration: InputDecoration(
                      hintText: 'Contoh: saya butuh surat domisili untuk buka rekening bank…',
                      counterText: '${_pesanController.text.length}/$_maxPesan',
                      filled: true,
                      fillColor: Colors.white,
                      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Padding(
                  padding: const EdgeInsets.only(bottom: 22),
                  child: SizedBox(
                    width: 48,
                    height: 48,
                    child: FilledButton(
                      onPressed: _loadingAi ? null : _kirimPesan,
                      style: FilledButton.styleFrom(
                        padding: EdgeInsets.zero,
                        backgroundColor: AppColors.primaryBrand,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                      ),
                      child: const Icon(Icons.send_rounded, size: 20, semanticLabel: 'Kirim ke asisten'),
                    ),
                  ),
                ),
              ],
            ),
            TextButton(
              onPressed: () => context.push(RouteNames.wargaPengajuanManual),
              child: const Text('Isi formulir manual saja'),
            ),
          ],
        ),
      );

  // ---- Langkah 2: Hasil isian

  Widget _buildHasil() {
    final types = ref.watch(letterTypesProvider).valueOrNull ?? const <Map<String, dynamic>>[];
    final kurang = _kurang;

    return Column(
      children: [
        Expanded(
          child: Form(
            key: _formKey,
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                _kartuJenis(types),
                const SizedBox(height: 14),
                _legenda(),
                const SizedBox(height: 14),
                if (kurang.isNotEmpty) ...[_bannerKurang(kurang), const SizedBox(height: 14)],
                _sectionSuratIni(),
                const SizedBox(height: 14),
                _sectionBiodata(),
              ],
            ),
          ),
        ),
        _footer(
          primary: RTPrimaryButton(
            text: 'Lanjut ke Pratinjau',
            trailingIcon: Icons.arrow_forward_rounded,
            onPressed: _lanjutKePratinjau,
          ),
          secondaryLabel: 'Ceritakan ulang ke asisten',
          onSecondary: () => setState(() => _step = _Step.asisten),
        ),
      ],
    );
  }

  Widget _kartuJenis(List<Map<String, dynamic>> types) => Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(color: AppColors.primaryBrand, borderRadius: BorderRadius.circular(16)),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              Container(
                width: 40, height: 40,
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.16),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(Icons.description_outlined, color: Colors.white, size: 20),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Jenis surat', style: AppTypography.caption.copyWith(color: AppColors.primaryContainer)),
                    Text(_namaJenis(types),
                        style: AppTypography.titleSmall.copyWith(color: Colors.white, fontSize: 16)),
                  ],
                ),
              ),
              PopupMenuButton<int>(
                tooltip: 'Ganti jenis surat',
                icon: const Icon(Icons.edit_outlined, color: Colors.white, size: 20),
                onSelected: (id) => setState(() {
                  _jenisSuratId = id;
                  _jenisDariAi = false;
                }),
                itemBuilder: (_) => [
                  for (final t in types)
                    PopupMenuItem<int>(value: t['jenis_surat_id'] as int, child: Text(t['nama_surat'].toString())),
                ],
              ),
            ]),
            const SizedBox(height: 12),
            TextFormField(
              controller: _keperluanController,
              maxLines: 2,
              minLines: 1,
              style: AppTypography.bodyMedium.copyWith(color: Colors.white),
              cursorColor: Colors.white,
              onChanged: (_) => setState(() => _keperluanDariAi = false),
              validator: (v) => (v == null || v.trim().length < 5) ? 'Keperluan wajib diisi' : null,
              decoration: InputDecoration(
                labelText: 'Keperluan',
                labelStyle: const TextStyle(color: AppColors.primaryContainer),
                floatingLabelStyle: const TextStyle(color: AppColors.primaryContainer),
                errorStyle: const TextStyle(color: Color(0xFFFDE68A)),
                filled: true,
                fillColor: Colors.white.withValues(alpha: 0.10),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.3)),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: const BorderSide(color: Colors.white),
                ),
                errorBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: const BorderSide(color: Color(0xFFFDE68A)),
                ),
                focusedErrorBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: const BorderSide(color: Color(0xFFFDE68A)),
                ),
              ),
            ),
            if (_jenisDariAi || _keperluanDariAi) ...[
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(999)),
                child: Text('Diisi AI dari ceritamu',
                    style: AppTypography.labelSmall.copyWith(color: _aiFg, fontWeight: FontWeight.w700)),
              ),
            ],
          ],
        ),
      );

  Widget _badge(_Sumber s) {
    final (label, bg, fg) = switch (s) {
      _Sumber.ai => ('AI', _aiBg, _aiFg),
      _Sumber.tersimpan => ('Tersimpan', _savedBg, _savedFg),
      _Sumber.bawaan => ('Bawaan', AppColors.surfaceAlt, AppColors.textSlate),
      _Sumber.kosong => ('Perlu diisi', _missingBg, _missingFg),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(999)),
      child: Text(label, style: AppTypography.labelSmall.copyWith(color: fg, fontSize: 10, fontWeight: FontWeight.w700)),
    );
  }

  Widget _legenda() => Wrap(
        spacing: 8,
        runSpacing: 6,
        crossAxisAlignment: WrapCrossAlignment.center,
        children: [
          Text('Sumber isian:', style: AppTypography.labelSmall.copyWith(color: AppColors.textSecondary)),
          _badge(_Sumber.ai),
          _badge(_Sumber.tersimpan),
          _badge(_Sumber.kosong),
        ],
      );

  Widget _bannerKurang(List<String> kurang) => Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: const Color(0xFFFFFBEB),
          border: Border.all(color: const Color(0xFFFDE68A)),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Icon(Icons.info_outline_rounded, size: 18, color: Color(0xFFB45309)),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                (_pertanyaan?.isNotEmpty ?? false)
                    ? _pertanyaan!
                    : 'Tinggal lengkapi: ${kurang.join(', ')}.',
                style: AppTypography.bodySmall.copyWith(color: const Color(0xFF78350F), height: 1.5),
              ),
            ),
          ],
        ),
      );

  Widget _card({required Widget child}) => Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          border: Border.all(color: AppColors.border),
          borderRadius: BorderRadius.circular(16),
        ),
        child: child,
      );

  InputDecoration _dekor(String hint) => InputDecoration(
        hintText: hint,
        isDense: true,
        filled: true,
        fillColor: Colors.white,
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.borderSubtle),
        ),
      );

  Widget _label(String text, {_Sumber? sumber}) => Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: Row(children: [
          Expanded(
            child: Text(text, style: AppTypography.labelMedium.copyWith(color: AppColors.textSlate, fontSize: 12)),
          ),
          if (sumber != null) _badge(sumber),
        ]),
      );

  Widget _sectionSuratIni() => _card(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Untuk surat ini', style: AppTypography.labelLarge.copyWith(fontWeight: FontWeight.w700)),
            const SizedBox(height: 12),
            _label('Tujuan surat *',
                sumber: _tujuanController.text.trim().isEmpty ? _Sumber.kosong : _sumber['tujuan']),
            TextFormField(
              controller: _tujuanController,
              onChanged: (_) => setState(() => _sumber.remove('tujuan')),
              validator: (v) => (v == null || v.trim().isEmpty) ? 'Tujuan surat wajib diisi' : null,
              decoration: _dekor('Contoh: Polrestabes Surabaya'),
            ),
            const SizedBox(height: 12),
            _label('Keterangan lain (opsional)'),
            TextFormField(
              controller: _keteranganController,
              maxLines: 2,
              minLines: 1,
              decoration: _dekor('Isi bila ada keterangan tambahan'),
            ),
            const SizedBox(height: 12),
            _label('Tanda tangan'),
            Row(children: [
              Expanded(child: _pilihanTtd('digital', 'Digital (PDF)')),
              const SizedBox(width: 8),
              Expanded(child: _pilihanTtd('basah', 'Basah (cetak)')),
            ]),
          ],
        ),
      );

  Widget _pilihanTtd(String value, String label) {
    final selected = _metodeTtd == value;
    return OutlinedButton(
      onPressed: () => setState(() => _metodeTtd = value),
      style: OutlinedButton.styleFrom(
        minimumSize: const Size.fromHeight(44),
        backgroundColor: selected ? AppColors.primaryBg : Colors.white,
        side: BorderSide(color: selected ? AppColors.primaryAction : AppColors.borderSubtle, width: selected ? 1.5 : 1),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
      child: Text(
        label,
        style: AppTypography.labelMedium.copyWith(
          color: selected ? AppColors.primaryBrand : AppColors.textSlate,
          fontWeight: selected ? FontWeight.w700 : FontWeight.w600,
        ),
      ),
    );
  }

  Widget _sectionBiodata() {
    final user = ref.watch(authControllerProvider).user;
    final kk = _nomorKkController.text.trim();
    final kkTersamar = kk.length == 16 ? '${kk.substring(0, 4)} •••• •••• ${kk.substring(12)}' : kk;
    final ringkas = <(String, String, String)>[
      ('Nama', user?.namaLengkap ?? '-', ''),
      ('Pekerjaan', _pekerjaanController.text, 'pekerjaan'),
      ('Tempat, tgl lahir', '${_tempatLahirController.text}, ${_tanggalPanjang(_tanggalLahir)}', 'tempat_lahir'),
      ('Jenis kelamin', _jenisKelamin ?? '', 'jenis_kelamin'),
      ('Status kawin', _statusKawin ?? '', 'status_kawin'),
      ('Agama', _agama ?? '', 'agama'),
      ('Kewarganegaraan', _kewarganegaraanController.text, 'kewarganegaraan'),
      ('No. KK', kkTersamar, 'nomor_kk'),
    ];

    return _card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(_editBiodata ? 'Biodata pemohon' : 'Biodata tersimpan',
                      style: AppTypography.labelLarge.copyWith(fontWeight: FontWeight.w700)),
                  Text(
                    _editBiodata
                        ? 'Diisi sekali, dipakai lagi untuk surat berikutnya'
                        : 'Dari pengajuan sebelumnya, tidak perlu diisi ulang',
                    style: AppTypography.caption.copyWith(color: AppColors.textMuted),
                  ),
                ],
              ),
            ),
            if (!_editBiodata)
              TextButton(onPressed: () => setState(() => _editBiodata = true), child: const Text('Ubah')),
          ]),
          const SizedBox(height: 8),
          if (!_editBiodata)
            for (final (label, value, key) in ringkas)
              Container(
                padding: const EdgeInsets.symmetric(vertical: 9),
                decoration: const BoxDecoration(border: Border(top: BorderSide(color: Color(0xFFF1F5F9)))),
                child: Row(children: [
                  SizedBox(
                    width: 116,
                    child: Text(label, style: AppTypography.caption.copyWith(color: AppColors.textMuted)),
                  ),
                  Expanded(
                    child: Text(value,
                        style: AppTypography.bodySmall.copyWith(fontWeight: FontWeight.w600, color: AppColors.textPrimary)),
                  ),
                  if (_sumber[key] != null) _badge(_sumber[key]!),
                ]),
              )
          else
            ..._formBiodata(),
        ],
      ),
    );
  }

  List<Widget> _formBiodata() {
    Widget gap() => const SizedBox(height: 12);
    Widget dropdown(String label, String key, String? value, List<String> opts, ValueChanged<String?> onChanged) =>
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _label('$label *', sumber: value == null ? _Sumber.kosong : _sumber[key]),
            DropdownButtonFormField<String>(
              key: ValueKey('$key-$value'),
              initialValue: value,
              isExpanded: true,
              decoration: _dekor('Pilih ${label.toLowerCase()}'),
              items: [for (final o in opts) DropdownMenuItem(value: o, child: Text(o))],
              onChanged: (v) {
                _sumber.remove(key);
                onChanged(v);
              },
              validator: (v) => v == null ? '$label wajib dipilih' : null,
            ),
          ],
        );
    Widget teks(String label, String key, TextEditingController c,
            {String hint = '', TextInputType? type, String? Function(String?)? validator, int? maxLength}) =>
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _label('$label *', sumber: c.text.trim().isEmpty ? _Sumber.kosong : _sumber[key]),
            TextFormField(
              controller: c,
              keyboardType: type,
              maxLength: maxLength,
              inputFormatters: type == TextInputType.number ? [FilteringTextInputFormatter.digitsOnly] : null,
              onChanged: (_) => setState(() => _sumber.remove(key)),
              validator: validator ?? (v) => (v == null || v.trim().isEmpty) ? '$label wajib diisi' : null,
              decoration: _dekor(hint).copyWith(counterText: ''),
            ),
          ],
        );

    return [
      teks('Pekerjaan', 'pekerjaan', _pekerjaanController, hint: 'Contoh: Karyawan Swasta'),
      gap(),
      dropdown('Jenis Kelamin', 'jenis_kelamin', _jenisKelamin, _jenisKelaminOptions,
          (v) => setState(() => _jenisKelamin = v)),
      gap(),
      teks('Tempat Lahir', 'tempat_lahir', _tempatLahirController, hint: 'Contoh: Surabaya'),
      gap(),
      _label('Tanggal Lahir *', sumber: _tanggalLahir == null ? _Sumber.kosong : _sumber['tanggal_lahir']),
      OutlinedButton.icon(
        onPressed: _pilihTanggalLahir,
        icon: const Icon(Icons.calendar_today_outlined, size: 18),
        label: Align(
          alignment: Alignment.centerLeft,
          child: Text(_tanggalLahir == null ? 'Pilih tanggal lahir' : _tanggalPanjang(_tanggalLahir)),
        ),
        style: OutlinedButton.styleFrom(
          minimumSize: const Size.fromHeight(46),
          foregroundColor: AppColors.textPrimary,
          side: BorderSide(color: _tanggalLahir == null ? AppColors.warning : AppColors.borderSubtle),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      ),
      gap(),
      dropdown('Agama', 'agama', _agama, _agamaOptions, (v) => setState(() => _agama = v)),
      gap(),
      dropdown('Status Perkawinan', 'status_kawin', _statusKawin, _statusKawinOptions,
          (v) => setState(() => _statusKawin = v)),
      gap(),
      teks('Kewarganegaraan', 'kewarganegaraan', _kewarganegaraanController, hint: 'WNI'),
      gap(),
      teks('Nomor Kartu Keluarga (KK)', 'nomor_kk', _nomorKkController,
          hint: '16 digit angka',
          type: TextInputType.number,
          maxLength: 16,
          validator: (v) =>
              RegExp(r'^\d{16}$').hasMatch(v?.trim() ?? '') ? null : 'Nomor KK harus 16 digit angka'),
      if (_biodataLengkap)
        Align(
          alignment: Alignment.centerRight,
          child: TextButton(
            onPressed: () => setState(() => _editBiodata = false),
            child: const Text('Selesai ubah'),
          ),
        ),
    ];
  }

  // ---- Langkah 3: Konfirmasi

  Widget _buildKonfirmasi() {
    final user = ref.watch(authControllerProvider).user;
    final types = ref.watch(letterTypesProvider).valueOrNull ?? const <Map<String, dynamic>>[];
    final submitting = ref.watch(letterSubmitControllerProvider).isLoading;
    final alamat = '${user?.alamat ?? '-'}, RT ${SuratIdentitas.rt} / RW ${SuratIdentitas.rw}';

    return Column(
      children: [
        Expanded(
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text('Pratinjau surat', style: AppTypography.labelLarge.copyWith(fontWeight: FontWeight.w700)),
              const SizedBox(height: 8),
              BlangkoPreview(
                nama: user?.namaLengkap ?? '-',
                alamat: alamat,
                pekerjaan: _pekerjaanController.text.trim(),
                jenisKelamin: _jenisKelamin ?? '',
                tempatTglLahir: '${_tempatLahirController.text.trim()}, ${_tanggalPanjang(_tanggalLahir)}',
                agama: _agama ?? '',
                statusKawin: _statusKawin ?? '',
                kewarganegaraan: _kewarganegaraanController.text.trim(),
                kkKtp: '${_nomorKkController.text.trim()} / ${user?.nik ?? '-'}',
                tujuan: _tujuanController.text.trim(),
                keperluan: _keperluanController.text.trim(),
                keteranganLain: _keteranganController.text.trim(),
              ),
              const SizedBox(height: 8),
              Text(
                'Format mengikuti blangko resmi Surat Pengantar / Keterangan RT ${SuratIdentitas.rt}. '
                'Nomor surat dan tanda tangan Ketua RT diisi otomatis setelah disetujui.',
                style: AppTypography.caption.copyWith(color: AppColors.textMuted, height: 1.5),
              ),
              const SizedBox(height: 14),
              _card(
                child: Column(children: [
                  _barisRingkas('Jenis surat', _namaJenis(types), first: true),
                  _barisRingkas('Tanda tangan', _metodeTtd == 'digital' ? 'Digital (PDF)' : 'Basah (cetak)'),
                  _barisRingkas('Status', 'Menunggu persetujuan Ketua RT'),
                ]),
              ),
              const SizedBox(height: 14),
              _card(
                child: CheckboxListTile(
                  value: _setuju,
                  onChanged: (v) => setState(() => _setuju = v ?? false),
                  contentPadding: EdgeInsets.zero,
                  controlAffinity: ListTileControlAffinity.leading,
                  activeColor: AppColors.primaryBrand,
                  title: Text(
                    'Saya menyatakan data di atas benar dan sudah saya periksa, termasuk isian dari asisten AI.',
                    style: AppTypography.bodySmall.copyWith(color: AppColors.textSlate, height: 1.5),
                  ),
                ),
              ),
            ],
          ),
        ),
        _footer(
          primary: RTPrimaryButton(
            text: 'Ajukan Surat',
            icon: Icons.send_rounded,
            isLoading: submitting,
            onPressed: (_setuju && !submitting) ? _ajukan : null,
          ),
          secondaryLabel: 'Ubah data',
          onSecondary: submitting ? null : () => setState(() => _step = _Step.hasil),
        ),
      ],
    );
  }

  Widget _barisRingkas(String label, String value, {bool first = false}) => Container(
        padding: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(
          border: first ? null : const Border(top: BorderSide(color: Color(0xFFF1F5F9))),
        ),
        child: Row(children: [
          SizedBox(width: 110, child: Text(label, style: AppTypography.caption.copyWith(color: AppColors.textMuted))),
          Expanded(
            child: Text(value, style: AppTypography.bodySmall.copyWith(fontWeight: FontWeight.w600)),
          ),
        ]),
      );

  Widget _footer({required Widget primary, required String secondaryLabel, VoidCallback? onSecondary}) => Container(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
        decoration: const BoxDecoration(
          color: Colors.white,
          border: Border(top: BorderSide(color: AppColors.border)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            primary,
            TextButton(onPressed: onSecondary, child: Text(secondaryLabel)),
          ],
        ),
      );
}
