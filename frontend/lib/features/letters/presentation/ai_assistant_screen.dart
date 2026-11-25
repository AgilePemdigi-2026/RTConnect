import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
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

  // Percakapan lanjutan & evaluasi AI
  static const _maxRiwayat = 4;
  final List<String> _riwayat = []; // pesan warga yang sudah diproses AI
  final Set<String> _diubahManual = {}; // kolom yang diubah/diisi sendiri oleh warga
  Map<String, String> _nilaiAi = {}; // kolom -> nilai dari AI (untuk catatan ketepatan)
  String? _modelAi;
  bool _tanyaLanjut = false; // asisten menunggu jawaban lanjutan di chat
  List<String> _tujuanSaran = const [];
  List<String> _syarat = const [];
  PlatformFile? _lampiran;
  String? _lampiranNama;

  // Biodata tersimpan (dicek saat layar dibuka) -> peringatan bila belum lengkap
  bool _biodataChecked = false;
  bool _wargaBaru = false;
  List<String> _biodataKurang = const [];
  static const _labelBiodata = {
    'pekerjaan': 'Pekerjaan',
    'jenis_kelamin': 'Jenis kelamin',
    'tempat_lahir': 'Tempat lahir',
    'tanggal_lahir': 'Tanggal lahir',
    'agama': 'Agama',
    'status_kawin': 'Status perkawinan',
    'kewarganegaraan': 'Kewarganegaraan',
    'nomor_kk': 'Nomor KK',
  };
  static const _contohCeritaLengkap =
      'Saya butuh surat pengantar SKCK untuk melamar kerja di PT Maju Jaya. '
      'Saya laki-laki, lahir di Surabaya 12 Mei 2001, karyawan swasta, belum kawin.';

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
  // Guardrail AI: isian yang ditolak server (tidak disebut / melanggar SOP) & peringatan
  List<Map<String, String>> _ditolak = [];
  List<String> _peringatan = [];

  // Langkah 3
  bool _setuju = false;

  @override
  void initState() {
    super.initState();
    _cekBiodataTersimpan();
  }

  Future<void> _cekBiodataTersimpan() async {
    try {
      final data = await ref.read(letterRepositoryProvider).getMyLastApplicantData();
      if (!mounted) return;
      final kurang = <String>[];
      if (data != null) {
        for (final entry in _labelBiodata.entries) {
          final value = data[entry.key]?.toString().trim() ?? '';
          final invalidKk = entry.key == 'nomor_kk' && !RegExp(r'^\d{16}$').hasMatch(value);
          if (value.isEmpty || invalidKk) kurang.add(entry.value);
        }
      }
      setState(() {
        _wargaBaru = data == null;
        _biodataKurang = kurang;
        _biodataChecked = true;
      });
    } catch (_) {
      // Gagal cek tidak menghalangi pengajuan; kekurangan tetap ditandai di layar Hasil.
    }
  }

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
      final result = await ref
          .read(letterRepositoryProvider)
          .aiFill(pesan, riwayat: _riwayat.length > _maxRiwayat
              ? _riwayat.sublist(_riwayat.length - _maxRiwayat)
              : List.of(_riwayat));
      if (!mounted) return;
      _riwayat.add(pesan);
      _terapkanHasil(result);
      // Peringatan guardrail (mis. perintah sisipan diabaikan) ditampilkan di chat
      for (final p in _peringatan) {
        _messages.add(_ChatMessage(p, isError: true));
      }
      final aiDipakai = result['ai_digunakan'] == true;
      // Percakapan lanjutan: bila jenis/keperluan/tujuan masih kosong, asisten bertanya di chat.
      final belumJelas = [
        if (_jenisSuratId == null) 'jenis surat',
        if (_keperluanController.text.trim().isEmpty) 'keperluan',
        if (_tujuanController.text.trim().isEmpty) 'tujuan surat',
      ];
      final lanjut = aiDipakai && belumJelas.isNotEmpty && _riwayat.length <= _maxRiwayat;
      setState(() {
        _loadingAi = false;
        if (lanjut) {
          _tanyaLanjut = true;
          _messages.add(_ChatMessage(_pertanyaan?.isNotEmpty == true
              ? _pertanyaan!
              : (belumJelas.length == 1 && belumJelas.first == 'tujuan surat'
                  ? 'Surat ini akan diserahkan ke instansi mana?'
                  : 'Boleh lengkapi ${belumJelas.join(' dan ')}-nya?')));
        } else {
          _tanyaLanjut = false;
          _messages.add(_ChatMessage(aiDipakai
              ? 'Formulir sudah saya isi. Silakan periksa dulu sebelum diajukan.'
              : (result['pesan']?.toString() ??
                  'Asisten AI sedang tidak tersedia. Formulir diisi dari data sebelumnya.')));
          _step = _Step.hasil;
        }
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

    bool bebas(String key) => !_diubahManual.contains(key); // isian warga tidak ditimpa AI
    void isi(TextEditingController c, String key, String value, {bool keepIfEmpty = false}) {
      if (!bebas(key)) return;
      if (value.isEmpty && keepIfEmpty) return;
      c.text = value;
    }

    final jenis = r['jenis_surat'] == null ? null : Map<String, dynamic>.from(r['jenis_surat'] as Map);
    if (bebas('jenis_surat') && jenis != null) {
      _jenisSuratId = jenis['jenis_surat_id'] as int?;
      _jenisDariAi = true;
    }
    final keperluan = r['keperluan']?.toString() ?? '';
    if (bebas('keperluan') && keperluan.isNotEmpty) {
      _keperluanController.text = keperluan;
      _keperluanDariAi = true;
    }
    final metode = r['metode_tanda_tangan']?.toString();
    if (bebas('metode_tanda_tangan') && (metode == 'digital' || metode == 'basah')) _metodeTtd = metode!;

    isi(_pekerjaanController, 'pekerjaan', text('pekerjaan'));
    isi(_tempatLahirController, 'tempat_lahir', text('tempat_lahir'));
    isi(_kewarganegaraanController, 'kewarganegaraan',
        text('kewarganegaraan').isEmpty ? 'WNI' : text('kewarganegaraan'));
    isi(_nomorKkController, 'nomor_kk', text('nomor_kk'));
    isi(_tujuanController, 'tujuan', text('tujuan'), keepIfEmpty: true);
    isi(_keteranganController, 'keterangan_lain', text('keterangan_lain'), keepIfEmpty: true);
    if (bebas('jenis_kelamin')) _jenisKelamin = option('jenis_kelamin', _jenisKelaminOptions);
    if (bebas('agama')) _agama = option('agama', _agamaOptions);
    if (bebas('status_kawin')) _statusKawin = option('status_kawin', _statusKawinOptions);
    if (bebas('tanggal_lahir')) _tanggalLahir = DateTime.tryParse(text('tanggal_lahir'));

    // Panduan jenis surat (pilihan tujuan cepat & dokumen yang perlu disiapkan)
    final panduan = r['panduan'] is Map ? Map<String, dynamic>.from(r['panduan'] as Map) : null;
    if (panduan != null) {
      _tujuanSaran = [for (final t in (panduan['tujuan_saran'] as List? ?? const [])) t.toString()];
      _syarat = [for (final t in (panduan['syarat'] as List? ?? const [])) t.toString()];
    }
    _modelAi = r['model']?.toString() ?? _modelAi;

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
      if (s != null && !_diubahManual.contains(f)) _sumber[f] = s;
    }
    // Catat nilai yang diisi AI untuk menghitung ketepatan saat pengajuan dikirim.
    if (r['ai_digunakan'] == true) {
      _nilaiAi = {
        for (final f in [..._biodataFields, 'tujuan', 'keterangan_lain'])
          if (_sumber[f] == _Sumber.ai) f: _nilaiSekarang(f),
        if (_jenisDariAi && _jenisSuratId != null) 'jenis_surat': _nilaiSekarang('jenis_surat'),
        if (_keperluanDariAi) 'keperluan': _nilaiSekarang('keperluan'),
      };
    }
    _sudahDiisi = true;
    _pertanyaan = r['pertanyaan']?.toString();
    _peringatan = [for (final p in (r['peringatan'] as List? ?? const [])) p.toString()];
    _ditolak = [
      for (final d in (r['ditolak'] as List? ?? const []))
        if (d is Map) {'kolom': '${d['kolom'] ?? ''}', 'alasan': '${d['alasan'] ?? ''}'}
    ];
    // Biodata lengkap -> tampil ringkas; ada yang kosong -> langsung bisa diisi.
    _editBiodata = !_biodataLengkap;
    _setuju = false;
  }

  String _nilaiSekarang(String key) => switch (key) {
        'jenis_surat' => '${_jenisSuratId ?? ''}',
        'keperluan' => _keperluanController.text.trim(),
        'tujuan' => _tujuanController.text.trim(),
        'keterangan_lain' => _keteranganController.text.trim(),
        'pekerjaan' => _pekerjaanController.text.trim(),
        'tempat_lahir' => _tempatLahirController.text.trim(),
        'kewarganegaraan' => _kewarganegaraanController.text.trim(),
        'nomor_kk' => _nomorKkController.text.trim(),
        'jenis_kelamin' => _jenisKelamin ?? '',
        'agama' => _agama ?? '',
        'status_kawin' => _statusKawin ?? '',
        'tanggal_lahir' => _tanggalLahir == null ? '' : _isoTanggal(_tanggalLahir!),
        _ => '',
      };

  void _tandaiManual(String key) {
    _diubahManual.add(key);
    _sumber.remove(key);
  }

  /// Catatan asisten AI yang dikirim bersama pengajuan (untuk statistik ketepatan AI).
  Map<String, dynamic>? get _aiMeta {
    if (_modelAi == null || _nilaiAi.isEmpty) return null;
    return {
      'model': _modelAi,
      'jumlah_pesan': _riwayat.isEmpty ? 1 : _riwayat.length,
      'kolom_ai': _nilaiAi.keys.toList(),
      'kolom_diubah': [
        for (final e in _nilaiAi.entries)
          if (_nilaiSekarang(e.key) != e.value) e.key,
      ],
    };
  }

  Future<void> _pilihLampiran() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf', 'png', 'jpg', 'jpeg'],
      withData: kIsWeb, // di web path file tidak tersedia, jadi isi file diambil langsung
    );
    if (result != null && result.files.isNotEmpty) {
      setState(() {
        _lampiran = result.files.single;
        _lampiranNama = result.files.single.name;
      });
    }
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
          lampiran: _lampiran,
          aiMeta: _aiMeta,
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
        _tandaiManual('tanggal_lahir');
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
                if (i == 0) _biodataNotice(),
                if (i == 0 && _messages.length == 1) _quickChips(),
                const SizedBox(height: 14),
              ],
              // Jawaban cepat untuk pertanyaan tujuan surat
              if (_tanyaLanjut && !_loadingAi && _tujuanSaran.isNotEmpty && _tujuanController.text.trim().isEmpty)
                Padding(
                  padding: const EdgeInsets.only(left: 42, bottom: 14),
                  child: Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      for (final t in _tujuanSaran)
                        ActionChip(
                          label: Text(t),
                          labelStyle: AppTypography.labelMedium.copyWith(color: AppColors.primaryBrand, fontSize: 13),
                          backgroundColor: AppColors.primaryBg,
                          side: const BorderSide(color: AppColors.primaryContainer),
                          shape: const StadiumBorder(),
                          onPressed: () {
                            _pesanController.text = t;
                            _kirimPesan();
                          },
                        ),
                    ],
                  ),
                ),
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

  /// Warga lama dengan biodata tersimpan yang belum lengkap -> peringatan.
  /// Warga baru -> contoh cerita lengkap yang bisa langsung dipakai.
  Widget _biodataNotice() {
    if (!_biodataChecked || (!_wargaBaru && _biodataKurang.isEmpty)) return const SizedBox.shrink();

    final sensitif = _biodataKurang.where((f) => f == 'Agama' || f == 'Nomor KK').toList();
    final bisaDiceritakan = _biodataKurang.where((f) => !sensitif.contains(f)).toList();
    final (bg, border, fg, icon, judul) = _wargaBaru
        ? (AppColors.primaryBg, AppColors.primaryContainer, const Color(0xFF1E3A8A),
            Icons.lightbulb_outline_rounded, 'Belum ada biodata tersimpan')
        : (const Color(0xFFFFFBEB), const Color(0xFFFDE68A), const Color(0xFF78350F),
            Icons.warning_amber_rounded, 'Biodata tersimpan belum lengkap');

    return Padding(
      padding: const EdgeInsets.only(left: 42, top: 12),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: bg,
          border: Border.all(color: border),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              Icon(icon, size: 18, color: fg),
              const SizedBox(width: 8),
              Expanded(
                child: Text(judul,
                    style: AppTypography.labelMedium.copyWith(color: fg, fontWeight: FontWeight.w700)),
              ),
            ]),
            const SizedBox(height: 6),
            if (_wargaBaru) ...[
              Text(
                'Sebutkan juga jenis kelamin, tempat & tanggal lahir, pekerjaan, dan status perkawinan '
                'di ceritamu. Contoh:',
                style: AppTypography.caption.copyWith(color: fg, height: 1.5),
              ),
              const SizedBox(height: 6),
              Text('"$_contohCeritaLengkap"',
                  style: AppTypography.caption.copyWith(color: fg, height: 1.5, fontStyle: FontStyle.italic)),
              Align(
                alignment: Alignment.centerLeft,
                child: TextButton(
                  onPressed: _loadingAi
                      ? null
                      : () => setState(() {
                            _pesanController.text = _contohCeritaLengkap;
                            _pesanController.selection =
                                TextSelection.collapsed(offset: _pesanController.text.length);
                          }),
                  child: const Text('Pakai contoh ini'),
                ),
              ),
            ] else ...[
              Text(
                'Belum terisi: ${_biodataKurang.join(', ')}.',
                style: AppTypography.caption.copyWith(color: fg, height: 1.5, fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 4),
              Text(
                [
                  if (bisaDiceritakan.isNotEmpty) 'Sebutkan ${bisaDiceritakan.join(', ').toLowerCase()} di ceritamu.',
                  if (sensitif.isNotEmpty)
                    '${sensitif.join(' dan ')} diisi di formulir pada langkah berikutnya (tidak dikirim ke AI).',
                ].join(' '),
                style: AppTypography.caption.copyWith(color: fg, height: 1.5),
              ),
            ],
          ],
        ),
      ),
    );
  }

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
                if (_ditolak.isNotEmpty) ...[_bannerDitolak(), const SizedBox(height: 14)],
                _sectionSuratIni(),
                const SizedBox(height: 14),
                _sectionSyarat(),
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
                  _tandaiManual('jenis_surat');
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
              onChanged: (_) => setState(() {
                _keperluanDariAi = false;
                _tandaiManual('keperluan');
              }),
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

  static const _labelKolom = {
    'jenis_surat': 'Jenis surat',
    'keperluan': 'Keperluan',
    'tujuan': 'Tujuan surat',
    'metode_tanda_tangan': 'Metode tanda tangan',
    'pekerjaan': 'Pekerjaan',
    'jenis_kelamin': 'Jenis kelamin',
    'tempat_lahir': 'Tempat lahir',
    'tanggal_lahir': 'Tanggal lahir',
    'status_kawin': 'Status perkawinan',
    'kewarganegaraan': 'Kewarganegaraan',
    'keterangan_lain': 'Keterangan lain',
  };

  // Transparansi guardrail: kolom yang sengaja TIDAK diisi AI beserta alasannya
  Widget _bannerDitolak() => Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: const Color(0xFFF1F5F9),
          border: Border.all(color: const Color(0xFFCBD5E1)),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.shield_outlined, size: 18, color: Color(0xFF475569)),
                const SizedBox(width: 8),
                Expanded(
                  child: Text('AI tidak mengisi kolom berikut, silakan isi sendiri',
                      style: AppTypography.bodySmall
                          .copyWith(color: const Color(0xFF334155), fontWeight: FontWeight.w600)),
                ),
              ],
            ),
            const SizedBox(height: 6),
            for (final d in _ditolak)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(
                  '• ${_labelKolom[d['kolom']] ?? d['kolom']}: ${d['alasan']}',
                  style: AppTypography.bodySmall.copyWith(color: const Color(0xFF475569), height: 1.4),
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

  /// Dokumen yang perlu disiapkan (dari panduan jenis surat) + unggah lampiran opsional.
  Widget _sectionSyarat() => _card(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Dokumen yang perlu disiapkan',
                style: AppTypography.labelLarge.copyWith(fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            if (_syarat.isEmpty)
              Text('Pilih jenis surat untuk melihat dokumen persyaratan.',
                  style: AppTypography.caption.copyWith(color: AppColors.textMuted))
            else
              for (final item in _syarat)
                Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    const Icon(Icons.check_circle_outline_rounded, size: 16, color: AppColors.primaryBrand),
                    const SizedBox(width: 8),
                    Expanded(child: Text(item, style: AppTypography.bodySmall)),
                  ]),
                ),
            const SizedBox(height: 8),
            if (_lampiranNama == null)
              OutlinedButton.icon(
                onPressed: _pilihLampiran,
                icon: const Icon(Icons.attach_file_rounded, size: 18),
                label: const Text('Unggah lampiran (opsional)'),
              )
            else
              Row(children: [
                const Icon(Icons.description_outlined, size: 18, color: AppColors.primaryBrand),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(_lampiranNama!, overflow: TextOverflow.ellipsis, style: AppTypography.bodySmall),
                ),
                IconButton(
                  tooltip: 'Hapus lampiran',
                  icon: const Icon(Icons.close_rounded, size: 18),
                  onPressed: () => setState(() {
                    _lampiran = null;
                    _lampiranNama = null;
                  }),
                ),
              ]),
          ],
        ),
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
              onChanged: (_) => setState(() => _tandaiManual('tujuan')),
              validator: (v) => (v == null || v.trim().isEmpty) ? 'Tujuan surat wajib diisi' : null,
              decoration: _dekor('Contoh: Polrestabes Surabaya'),
            ),
            if (_tujuanSaran.isNotEmpty) ...[
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 6,
                children: [
                  for (final t in _tujuanSaran)
                    ChoiceChip(
                      label: Text(t),
                      selected: _tujuanController.text.trim() == t,
                      onSelected: (_) => setState(() {
                        _tujuanController.text = t;
                        _tandaiManual('tujuan');
                      }),
                    ),
                ],
              ),
            ],
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
      onPressed: () => setState(() {
        _metodeTtd = value;
        _diubahManual.add('metode_tanda_tangan');
      }),
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
                _tandaiManual(key);
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
              onChanged: (_) => setState(() => _tandaiManual(key)),
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
                  _barisRingkas('Lampiran', _lampiranNama ?? '-'),
                  _barisRingkas('Status', 'Menunggu persetujuan Ketua RT'),
                ]),
              ),
              const SizedBox(height: 14),
              _card(
                // Material transparan: ListTile di dalam Container berwarna wajib punya Material sendiri.
                child: Material(
                  type: MaterialType.transparency,
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
