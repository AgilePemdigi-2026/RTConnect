enum StatusPengajuan {
  diajukan('Diajukan'),
  perluRevisi('Perlu Revisi'),
  ditolak('Ditolak'),
  disetujui('Disetujui'),
  siapDiambil('Siap Diambil'),
  diambil('Diambil'),
  selesai('Selesai');

  final String label;
  const StatusPengajuan(this.label);

  static StatusPengajuan fromString(String s) => StatusPengajuan.values
      .firstWhere((e) => e.label.toLowerCase() == s.toLowerCase(),
          orElse: () => StatusPengajuan.diajukan);
}

enum MetodeTtd { digital, basah }

class Pengajuan {
  final int id;
  final String nomorPengajuan; // contoh: SRT-101
  final String namaWarga;
  final String nikSamaran; // contoh: 350612••••••1234
  final String alamat;
  final String rtRw;
  final String jenisSurat;
  final String keperluan;
  final String? deskripsiKeperluan;
  final MetodeTtd metodeTtd;
  final DateTime tanggalPengajuan;
  final StatusPengajuan status;
  final String? catatanRevisi;
  final String? alasanPenolakan;
  final String? lampiranNama;
  final String? lampiranUkuran;
  final String? lampiranUrl;
  final String? drafSurat;
  final bool iuranLunas;

  const Pengajuan({
    required this.id,
    required this.nomorPengajuan,
    required this.namaWarga,
    required this.nikSamaran,
    required this.alamat,
    required this.rtRw,
    required this.jenisSurat,
    required this.keperluan,
    this.deskripsiKeperluan,
    required this.metodeTtd,
    required this.tanggalPengajuan,
    required this.status,
    this.catatanRevisi,
    this.alasanPenolakan,
    this.lampiranNama,
    this.lampiranUkuran,
    this.lampiranUrl,
    this.drafSurat,
    this.iuranLunas = false,
  });

  String get inisial {
    final p = namaWarga.trim().split(RegExp(r'\s+'));
    if (p.length == 1) return p.first.substring(0, 1).toUpperCase();
    return (p[0][0] + p[1][0]).toUpperCase();
  }

  factory Pengajuan.fromJson(Map<String, dynamic> j) => Pengajuan(
        id: j['pengajuan_id'] as int,
        nomorPengajuan: j['nomor_pengajuan'] ?? 'SRT-${j['pengajuan_id']}',
        namaWarga: j['nama_warga'] ?? '-',
        nikSamaran: j['nik_samaran'] ?? '-',
        alamat: j['alamat'] ?? '-',
        rtRw: j['rt_rw'] ?? 'RT 04 / RW 07',
        jenisSurat: j['jenis_surat'] ?? '-',
        keperluan: j['keperluan'] ?? '-',
        deskripsiKeperluan: j['deskripsi_keperluan'],
        metodeTtd: (j['metode_tanda_tangan'] ?? 'digital') == 'basah'
            ? MetodeTtd.basah
            : MetodeTtd.digital,
        tanggalPengajuan: DateTime.parse(j['tanggal_pengajuan']),
        status: StatusPengajuan.fromString(j['status'] ?? 'Diajukan'),
        catatanRevisi: j['catatan_revisi'],
        alasanPenolakan: j['alasan_penolakan'],
        lampiranNama: j['lampiran_nama'],
        lampiranUkuran: j['lampiran_ukuran'],
        lampiranUrl: j['berkas_lampiran_url'],
        drafSurat: j['draf_ai_konten'],
        iuranLunas: j['iuran_lunas'] == true,
      );

  Pengajuan copyWith({StatusPengajuan? status, String? catatanRevisi, String? alasanPenolakan}) =>
      Pengajuan(
        id: id,
        nomorPengajuan: nomorPengajuan,
        namaWarga: namaWarga,
        nikSamaran: nikSamaran,
        alamat: alamat,
        rtRw: rtRw,
        jenisSurat: jenisSurat,
        keperluan: keperluan,
        deskripsiKeperluan: deskripsiKeperluan,
        metodeTtd: metodeTtd,
        tanggalPengajuan: tanggalPengajuan,
        status: status ?? this.status,
        catatanRevisi: catatanRevisi ?? this.catatanRevisi,
        alasanPenolakan: alasanPenolakan ?? this.alasanPenolakan,
        lampiranNama: lampiranNama,
        lampiranUkuran: lampiranUkuran,
        lampiranUrl: lampiranUrl,
        drafSurat: drafSurat,
        iuranLunas: iuranLunas,
      );
}
