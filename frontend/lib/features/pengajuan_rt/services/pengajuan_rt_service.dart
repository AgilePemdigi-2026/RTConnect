import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/pengajuan.dart';

/// Hasil aksi ke backend (setuju/revisi/tolak/sahkan).
class AksiResult {
  final bool sukses;
  final String pesan;
  final int httpStatus;
  final String? nomorSurat;
  final int? sisaPercobaan;
  final int? sisaMenit;

  const AksiResult({
    required this.sukses,
    required this.pesan,
    this.httpStatus = 200,
    this.nomorSurat,
    this.sisaPercobaan,
    this.sisaMenit,
  });

  bool get terkunci => httpStatus == 423;

  factory AksiResult.fromResponse(http.Response r) {
    final j = jsonDecode(r.body) as Map<String, dynamic>;
    return AksiResult(
      sukses: j['status'] == 'success',
      pesan: j['message'] ?? '',
      httpStatus: r.statusCode,
      nomorSurat: j['nomor_surat'],
      sisaPercobaan: j['sisa_percobaan'],
      sisaMenit: j['sisa_menit'],
    );
  }
}

abstract class PengajuanRtService {
  Future<List<Pengajuan>> daftarPengajuan();
  Future<Pengajuan> detail(int id);
  Future<AksiResult> mintaRevisi(int id, String catatan);
  Future<AksiResult> tolak(int id, String alasan);
  Future<AksiResult> sahkanDigital(int id, String pin);
  Future<AksiResult> setujuiBasah(int id);
}

/// Implementasi asli ke backend Flask.
class ApiPengajuanRtService implements PengajuanRtService {
  final String baseUrl; // contoh: http://10.0.2.2:5000/api (emulator Android)
  final String Function() tokenProvider;

  ApiPengajuanRtService({required this.baseUrl, required this.tokenProvider});

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ${tokenProvider()}',
      };

  @override
  Future<List<Pengajuan>> daftarPengajuan() async {
    final r = await http.get(Uri.parse('$baseUrl/rt/pengajuan'), headers: _headers);
    if (r.statusCode != 200) throw Exception('Gagal memuat pengajuan (${r.statusCode})');
    final data = jsonDecode(r.body)['data'] as List;
    return data.map((e) => Pengajuan.fromJson(e)).toList();
  }

  @override
  Future<Pengajuan> detail(int id) async {
    final r = await http.get(Uri.parse('$baseUrl/rt/pengajuan/$id'), headers: _headers);
    if (r.statusCode != 200) throw Exception('Gagal memuat detail (${r.statusCode})');
    return Pengajuan.fromJson(jsonDecode(r.body)['data']);
  }

  Future<AksiResult> _post(String path, Map<String, dynamic> body) async {
    final r = await http.post(Uri.parse('$baseUrl$path'),
        headers: _headers, body: jsonEncode(body));
    return AksiResult.fromResponse(r);
  }

  @override
  Future<AksiResult> mintaRevisi(int id, String catatan) =>
      _post('/rt/pengajuan/$id/revisi', {'catatan_revisi': catatan});

  @override
  Future<AksiResult> tolak(int id, String alasan) =>
      _post('/rt/pengajuan/$id/tolak', {'alasan_penolakan': alasan});

  @override
  Future<AksiResult> sahkanDigital(int id, String pin) =>
      _post('/rt/pengajuan/$id/sahkan-digital', {'pin': pin});

  @override
  Future<AksiResult> setujuiBasah(int id) => _post('/rt/pengajuan/$id/setuju', {});
}

/// Data dummy untuk coba tampilan tanpa backend.
/// PIN dummy: 482913. Salah 5x -> terkunci.
class MockPengajuanRtService implements PengajuanRtService {
  static const _pinBenar = '482913';
  int _gagal = 0;
  DateTime? _lockedUntil;
  int _noUrut = 0;

  final List<Pengajuan> _data = [
    Pengajuan(
      id: 101,
      nomorPengajuan: 'SRT-101',
      namaWarga: 'Ahmad Dhafin Al Farisy',
      nikSamaran: '350612••••••1234',
      alamat: 'Griya Taman Asri Blok B No. 12, RT 04 / RW 07',
      rtRw: 'RT 04 / RW 07',
      jenisSurat: 'Surat Pengantar',
      keperluan: 'Pembuatan KTP Baru',
      deskripsiKeperluan:
          'Pemohon mengurus penggantian KTP karena pembaruan status & kepindahan wilayah dari RT 02 ke RT 04.',
      metodeTtd: MetodeTtd.digital,
      tanggalPengajuan: DateTime(2026, 8, 17, 9, 42),
      status: StatusPengajuan.diajukan,
      lampiranNama: 'ktp_lama_dhafin.pdf',
      lampiranUkuran: '842 KB',
      iuranLunas: true,
    ),
    Pengajuan(
      id: 100,
      nomorPengajuan: 'SRT-100',
      namaWarga: 'Mirza Diwa Luscakson',
      nikSamaran: '350612••••••5678',
      alamat: 'Griya Taman Asri Blok C No. 3, RT 04 / RW 07',
      rtRw: 'RT 04 / RW 07',
      jenisSurat: 'Surat Keterangan Domisili',
      keperluan: 'Administrasi Kampus',
      metodeTtd: MetodeTtd.basah,
      tanggalPengajuan: DateTime(2026, 8, 17, 8, 15),
      status: StatusPengajuan.selesai,
      iuranLunas: true,
    ),
    Pengajuan(
      id: 98,
      nomorPengajuan: 'SRT-098',
      namaWarga: 'Febrian Muhammad Yudhistira',
      nikSamaran: '350612••••••9012',
      alamat: 'Griya Taman Asri Blok A No. 7, RT 04 / RW 07',
      rtRw: 'RT 04 / RW 07',
      jenisSurat: 'Surat Keterangan Usaha',
      keperluan: 'Pengajuan KUR Mikro BRI',
      metodeTtd: MetodeTtd.digital,
      tanggalPengajuan: DateTime(2026, 8, 16, 19, 30),
      status: StatusPengajuan.perluRevisi,
      catatanRevisi: 'Menunggu kelengkapan foto tempat usaha terkini dari pemohon.',
    ),
    Pengajuan(
      id: 102,
      nomorPengajuan: 'SRT-102',
      namaWarga: 'Siti Rahmawati',
      nikSamaran: '350612••••••3344',
      alamat: 'Griya Taman Asri Blok D No. 1, RT 04 / RW 07',
      rtRw: 'RT 04 / RW 07',
      jenisSurat: 'Surat Pengantar SKCK',
      keperluan: 'Melamar Pekerjaan',
      metodeTtd: MetodeTtd.basah,
      tanggalPengajuan: DateTime(2026, 8, 18, 13, 5),
      status: StatusPengajuan.diajukan,
    ),
  ];

  Future<void> _delay() => Future.delayed(const Duration(milliseconds: 500));

  void _update(int id, Pengajuan Function(Pengajuan) f) {
    final i = _data.indexWhere((e) => e.id == id);
    _data[i] = f(_data[i]);
  }

  String _drafDummy(Pengajuan p) => 'Yang bertanda tangan di bawah ini Ketua RT 04 / RW 07 '
      'Kelurahan Tawangsari, menerangkan dengan sebenarnya bahwa:\n\n'
      'Nama    : ${p.namaWarga}\nNIK     : ${p.nikSamaran}\nAlamat  : ${p.alamat}\n'
      'Tujuan  : ${p.keperluan}\n\n'
      'Demikian surat pengantar ini kami buat dengan sebenarnya agar dapat '
      'dipergunakan sebagaimana mestinya.';

  @override
  Future<List<Pengajuan>> daftarPengajuan() async {
    await _delay();
    final l = [..._data]..sort((a, b) => b.tanggalPengajuan.compareTo(a.tanggalPengajuan));
    return l;
  }

  @override
  Future<Pengajuan> detail(int id) async {
    await _delay();
    final p = _data.firstWhere((e) => e.id == id);
    return Pengajuan(
      id: p.id,
      nomorPengajuan: p.nomorPengajuan,
      namaWarga: p.namaWarga,
      nikSamaran: p.nikSamaran,
      alamat: p.alamat,
      rtRw: p.rtRw,
      jenisSurat: p.jenisSurat,
      keperluan: p.keperluan,
      deskripsiKeperluan: p.deskripsiKeperluan,
      metodeTtd: p.metodeTtd,
      tanggalPengajuan: p.tanggalPengajuan,
      status: p.status,
      catatanRevisi: p.catatanRevisi,
      alasanPenolakan: p.alasanPenolakan,
      lampiranNama: p.lampiranNama,
      lampiranUkuran: p.lampiranUkuran,
      drafSurat: _drafDummy(p),
      iuranLunas: p.iuranLunas,
    );
  }

  @override
  Future<AksiResult> mintaRevisi(int id, String catatan) async {
    await _delay();
    _update(id, (p) => p.copyWith(status: StatusPengajuan.perluRevisi, catatanRevisi: catatan));
    return const AksiResult(sukses: true, pesan: 'Permintaan revisi berhasil dikirim');
  }

  @override
  Future<AksiResult> tolak(int id, String alasan) async {
    await _delay();
    _update(id, (p) => p.copyWith(status: StatusPengajuan.ditolak, alasanPenolakan: alasan));
    return const AksiResult(sukses: true, pesan: 'Pengajuan berhasil ditolak');
  }

  @override
  Future<AksiResult> sahkanDigital(int id, String pin) async {
    await _delay();
    final now = DateTime.now();
    if (_lockedUntil != null && _lockedUntil!.isAfter(now)) {
      final sisa = _lockedUntil!.difference(now).inMinutes + 1;
      return AksiResult(
          sukses: false,
          pesan: 'PIN terkunci. Coba lagi dalam $sisa menit.',
          httpStatus: 423,
          sisaMenit: sisa);
    }
    if (pin != _pinBenar) {
      _gagal++;
      if (_gagal >= 5) {
        _gagal = 0;
        _lockedUntil = now.add(const Duration(minutes: 15));
        return const AksiResult(
            sukses: false,
            pesan: 'PIN salah 5 kali. PIN dikunci selama 15 menit.',
            httpStatus: 423,
            sisaMenit: 15);
      }
      return AksiResult(
          sukses: false, pesan: 'PIN salah', httpStatus: 401, sisaPercobaan: 5 - _gagal);
    }
    _gagal = 0;
    _noUrut++;
    _update(id, (p) => p.copyWith(status: StatusPengajuan.selesai));
    return AksiResult(
      sukses: true,
      pesan: 'Tanda tangan digital berhasil disematkan',
      nomorSurat: '470/${_noUrut.toString().padLeft(3, '0')}/RT.04/X/2026',
    );
  }

  @override
  Future<AksiResult> setujuiBasah(int id) async {
    await _delay();
    _update(id, (p) => p.copyWith(status: StatusPengajuan.siapDiambil));
    return const AksiResult(sukses: true, pesan: 'Dokumen fisik siap diambil pemohon');
  }
}
