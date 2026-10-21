import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_typography.dart';
import '../../../shared/widgets/rt_primary_button.dart';
import '../../../shared/widgets/rt_status_badge.dart';
import '../../auth/presentation/auth_controller.dart';
import 'letter_controller.dart';
import 'widgets/pin_auth_dialog.dart';

/// Screen 10: Detail Pengajuan - Ketua RT & Warga (Figma Node #68:2063)
class LetterDetailScreen extends ConsumerStatefulWidget {
  final int applicationId;

  const LetterDetailScreen({super.key, required this.applicationId});

  @override
  ConsumerState<LetterDetailScreen> createState() => _LetterDetailScreenState();
}

class _LetterDetailScreenState extends ConsumerState<LetterDetailScreen> {
  final _resubmitController = TextEditingController();
  final _revisionNoteController = TextEditingController();
  final _rejectReasonController = TextEditingController();

  @override
  void dispose() {
    _resubmitController.dispose();
    _revisionNoteController.dispose();
    _rejectReasonController.dispose();
    super.dispose();
  }

  void _showResidentRevisionDialog(String currentKeperluan) {
    _resubmitController.text = currentKeperluan;
    showDialog<void>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: Text(
            'Perbaiki Isian Surat',
            style: AppTypography.heading3.copyWith(fontWeight: FontWeight.w700),
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Perbarui rincian keperluan surat sesuai arahan perbaikan dari Ketua RT:',
                style: AppTypography.caption.copyWith(color: AppColors.textSecondary),
              ),
              const SizedBox(height: AppSpacing.sm),
              TextField(
                controller: _resubmitController,
                maxLines: 4,
                decoration: InputDecoration(
                  hintText: 'Tuliskan perbaikan keperluan...',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  filled: true,
                  fillColor: const Color(0xFFF8FAFC),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: const Text('Batal'),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primaryAccent,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
              onPressed: () async {
                Navigator.pop(dialogContext);
                try {
                  final repo = ref.read(letterRepositoryProvider);
                  await repo.resubmitLetter(
                    widget.applicationId,
                    _resubmitController.text.trim(),
                  );
                  ref.invalidate(applicationDetailProvider(widget.applicationId));
                  if (!mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      backgroundColor: AppColors.success,
                      content: Text('Pengajuan berhasil diperbarui dan dikirim ulang ke RT'),
                    ),
                  );
                } catch (e) {
                  if (!mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(backgroundColor: AppColors.error, content: Text('Gagal: $e')),
                  );
                }
              },
              child: const Text('Kirim Ulang', style: TextStyle(color: Colors.white)),
            ),
          ],
        );
      },
    );
  }

  void _showRTRevisionDialog() {
    _revisionNoteController.clear();
    showDialog<void>(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: Text(
            'Minta Perbaikan ke Warga',
            style: AppTypography.heading3.copyWith(
              color: const Color(0xFFC2410C),
              fontWeight: FontWeight.w700,
            ),
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Tuliskan instruksi perbaikan yang jelas agar warga dapat memperbarui dokumen/keperluan.',
                style: AppTypography.caption,
              ),
              const SizedBox(height: AppSpacing.sm),
              TextField(
                controller: _revisionNoteController,
                maxLines: 4,
                decoration: InputDecoration(
                  hintText: 'Contoh: Mohon lampirkan scan KTP asli, foto buram...',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  filled: true,
                  fillColor: const Color(0xFFFFF7ED),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Batal'),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFEA580C),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
              onPressed: () async {
                final note = _revisionNoteController.text.trim();
                if (note.isEmpty) return;
                Navigator.pop(ctx);
                final success = await ref
                    .read(letterSubmitControllerProvider.notifier)
                    .submitDecision(widget.applicationId, 'revise', note);
                if (!mounted) return;
                if (success) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      backgroundColor: Color(0xFFEA580C),
                      content: Text('Catatan revisi telah dikirim ke warga.'),
                    ),
                  );
                }
              },
              child: const Text('Kirim Revisi', style: TextStyle(color: Colors.white)),
            ),
          ],
        );
      },
    );
  }

  void _showRTRejectDialog() {
    _rejectReasonController.clear();
    showDialog<void>(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: Text(
            'Tolak Permohonan Surat',
            style: AppTypography.heading3.copyWith(
              color: AppColors.error,
              fontWeight: FontWeight.w700,
            ),
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Berikan alasan penolakan permohonan surat ini secara transparan kepada warga.',
                style: AppTypography.caption,
              ),
              const SizedBox(height: AppSpacing.sm),
              TextField(
                controller: _rejectReasonController,
                maxLines: 4,
                decoration: InputDecoration(
                  hintText: 'Tuliskan alasan penolakan...',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  filled: true,
                  fillColor: const Color(0xFFFEF2F2),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Batal'),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.error,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
              onPressed: () async {
                final reason = _rejectReasonController.text.trim();
                if (reason.isEmpty) return;
                Navigator.pop(ctx);
                final success = await ref
                    .read(letterSubmitControllerProvider.notifier)
                    .submitDecision(widget.applicationId, 'reject', reason);
                if (!mounted) return;
                if (success) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      backgroundColor: AppColors.error,
                      content: Text('Permohonan surat telah ditolak.'),
                    ),
                  );
                }
              },
              child: const Text('Tolak Permohonan', style: TextStyle(color: Colors.white)),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final detailAsync = ref.watch(applicationDetailProvider(widget.applicationId));
    final authState = ref.watch(authControllerProvider);
    final user = authState.user;
    final isRT = user?.isRT ?? false;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: Text(
          'Detail Pengajuan',
          style: AppTypography.heading3.copyWith(
            color: AppColors.textPrimary,
            fontWeight: FontWeight.w800,
          ),
        ),
        centerTitle: false,
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(
            Icons.arrow_back_ios_new,
            color: AppColors.textPrimary,
            size: 20,
          ),
          onPressed: () => context.pop(),
        ),
        bottom: const PreferredSize(
          preferredSize: Size.fromHeight(1.0),
          child: Divider(height: 1.0, color: AppColors.border),
        ),
      ),
      body: SafeArea(
        child: detailAsync.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (err, _) => Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.error_outline, size: 48, color: AppColors.error),
                const SizedBox(height: AppSpacing.sm),
                Text('Gagal memuat rincian: $err', style: AppTypography.bodySmall),
                TextButton(
                  onPressed: () => ref.refresh(applicationDetailProvider(widget.applicationId)),
                  child: const Text('Muat Ulang'),
                ),
              ],
            ),
          ),
          data: (data) {
            final nomorPengajuan = data['nomor_pengajuan']?.toString() ?? '-';
            final nomorResmi = data['nomor_surat_resmi']?.toString();
            final namaSurat = data['nama_surat']?.toString() ?? 'Surat Pengantar RT';
            final status = data['status']?.toString().toLowerCase() ?? 'diajukan';
            final keperluan = data['keperluan']?.toString() ?? '-';
            final drafAi = data['draf_ai_konten']?.toString();
            final metode = data['metode_tanda_tangan']?.toString() ?? 'digital';
            final namaWarga = data['nama_lengkap']?.toString() ?? data['nama_warga']?.toString() ?? '-';
            final nik = data['nik']?.toString() ?? '-';
            final alamat = data['alamat']?.toString() ?? '-';
            final noTelepon = data['nomor_telepon']?.toString() ?? '0812-3456-7890';
            final catatanRevisi = data['catatan_revisi']?.toString() ?? data['catatan']?.toString();
            final alasanTolak = data['alasan_penolakan']?.toString();
            final lampiran = data['lampiran_url']?.toString();

            final isPending = status == 'diajukan' || status == 'diproses';
            final isDone = status == 'selesai' || status == 'disetujui';

            return Column(
              children: [
                Expanded(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(AppSpacing.lg),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        // Identitas Pemohon Card (Figma #68:2063)
                        _buildApplicantIdentityCard(
                          namaWarga: namaWarga,
                          nik: nik,
                          alamat: alamat,
                          noTelepon: noTelepon,
                          status: status,
                        ),
                        const SizedBox(height: AppSpacing.md),

                        // Bento Metadata Grid
                        _buildBentoMetadataBox(
                          nomorPengajuan: nomorPengajuan,
                          nomorResmi: nomorResmi,
                          namaSurat: namaSurat,
                          metode: metode,
                          keperluan: keperluan,
                        ),
                        const SizedBox(height: AppSpacing.md),

                        // Catatan Revisi Banner (if status is perlu_revisi)
                        if ((status == 'perlu revisi' || status == 'perlu_revisi') &&
                            catatanRevisi != null) ...[
                          _buildRevisionNotice(
                            catatan: catatanRevisi,
                            isRT: isRT,
                            currentKeperluan: keperluan,
                          ),
                          const SizedBox(height: AppSpacing.md),
                        ],

                        // Alasan Penolakan Banner (if status is ditolak)
                        if (status == 'ditolak' && alasanTolak != null) ...[
                          _buildRejectionNotice(alasan: alasanTolak),
                          const SizedBox(height: AppSpacing.md),
                        ],

                        // Dokumen Lampiran Berkas Box (if any)
                        _buildAttachmentPreviewBox(lampiran: lampiran),
                        const SizedBox(height: AppSpacing.lg),

                        // Realistic RT Official Letterhead Preview (Figma #68:2063)
                        _buildLetterheadPaperPreview(
                          namaSurat: namaSurat,
                          nomorResmi: nomorResmi ?? nomorPengajuan,
                          namaWarga: namaWarga,
                          nik: nik,
                          alamat: alamat,
                          keperluan: keperluan,
                          drafAi: drafAi,
                          status: status,
                          metode: metode,
                        ),
                        const SizedBox(height: 30),
                      ],
                    ),
                  ),
                ),

                // Sticky Bottom Action Bar
                _buildStickyBottomBar(
                  context,
                  isRT: isRT,
                  isPending: isPending,
                  isDone: isDone,
                  metode: metode,
                  namaWarga: namaWarga,
                  namaSurat: namaSurat,
                ),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _buildApplicantIdentityCard({
    required String namaWarga,
    required String nik,
    required String alamat,
    required String noTelepon,
    required String status,
  }) {
    final initials = namaWarga.isNotEmpty
        ? namaWarga
            .trim()
            .split(' ')
            .map((e) => e.isNotEmpty ? e[0] : '')
            .take(2)
            .join()
            .toUpperCase()
        : 'W';

    return Container(
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
        boxShadow: const [
          BoxShadow(
            color: Color(0x06000000),
            blurRadius: 8,
            offset: Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              CircleAvatar(
                radius: 24,
                backgroundColor: const Color(0xFFEFF6FF),
                child: Text(
                  initials,
                  style: AppTypography.heading3.copyWith(
                    color: AppColors.primaryAccent,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              const SizedBox(width: AppSpacing.md),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      namaWarga,
                      style: AppTypography.heading3.copyWith(
                        fontWeight: FontWeight.w800,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'NIK: $nik',
                      style: AppTypography.caption.copyWith(
                        color: AppColors.textSecondary,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
              RTStatusBadge(status: status),
            ],
          ),
          const SizedBox(height: AppSpacing.sm),
          const Divider(height: 1, color: AppColors.border),
          const SizedBox(height: AppSpacing.sm),

          // Resident Civic Tags
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: const Color(0xFFECFDF5),
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: const Color(0xFFA7F3D0)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.verified, size: 13, color: Color(0xFF059669)),
                    const SizedBox(width: 4),
                    Text(
                      'Warga Tetap RT 04',
                      style: AppTypography.caption.copyWith(
                        color: const Color(0xFF065F46),
                        fontWeight: FontWeight.w700,
                        fontSize: 11,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: const Color(0xFFEFF6FF),
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: const Color(0xFFBFDBFE)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.check_circle_outline, size: 13, color: Color(0xFF2563EB)),
                    const SizedBox(width: 4),
                    Text(
                      'Iuran RT: Lunas',
                      style: AppTypography.caption.copyWith(
                        color: const Color(0xFF1E40AF),
                        fontWeight: FontWeight.w700,
                        fontSize: 11,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.sm),

          // Address & Contact
          Row(
            children: [
              const Icon(Icons.location_on_outlined, size: 16, color: AppColors.textMuted),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  alamat,
                  style: AppTypography.caption.copyWith(color: AppColors.textSecondary),
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Row(
            children: [
              const Icon(Icons.phone_outlined, size: 16, color: AppColors.textMuted),
              const SizedBox(width: 6),
              Text(
                noTelepon,
                style: AppTypography.caption.copyWith(color: AppColors.textSecondary),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildBentoMetadataBox({
    required String nomorPengajuan,
    required String? nomorResmi,
    required String namaSurat,
    required String metode,
    required String keperluan,
  }) {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Informasi Permohonan',
            style: AppTypography.labelBold.copyWith(
              color: AppColors.textPrimary,
              fontSize: 14,
            ),
          ),
          const SizedBox(height: AppSpacing.sm),
          _buildInfoRow('Jenis Surat', namaSurat),
          _buildInfoRow('Nomor Pengajuan', nomorPengajuan),
          if (nomorResmi != null) _buildInfoRow('Nomor Surat Resmi', nomorResmi),
          _buildInfoRow(
            'Metode Tanda Tangan',
            metode == 'digital' ? 'Tanda Tangan Digital (QR Seal)' : 'Tanda Tangan Basah (Fisik)',
          ),
          _buildInfoRow('Keperluan', keperluan),
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 130,
            child: Text(
              label,
              style: AppTypography.caption.copyWith(color: AppColors.textMuted),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              value,
              style: AppTypography.caption.copyWith(
                fontWeight: FontWeight.w600,
                color: AppColors.textPrimary,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRevisionNotice({
    required String catatan,
    required bool isRT,
    required String currentKeperluan,
  }) {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF7ED),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFFED7AA), width: 1.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.warning_amber_rounded, color: Color(0xFFEA580C)),
              const SizedBox(width: 8),
              Text(
                'Catatan Perbaikan dari Ketua RT:',
                style: AppTypography.labelBold.copyWith(color: const Color(0xFFC2410C)),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            '"$catatan"',
            style: AppTypography.bodySmall.copyWith(
              color: const Color(0xFF7C2D12),
              fontStyle: FontStyle.italic,
            ),
          ),
          if (!isRT) ...[
            const SizedBox(height: AppSpacing.md),
            ElevatedButton.icon(
              onPressed: () => _showResidentRevisionDialog(currentKeperluan),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFEA580C),
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
              icon: const Icon(Icons.edit_note, size: 18),
              label: const Text('Perbaiki Isian Surat'),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildRejectionNotice({required String alasan}) {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: const Color(0xFFFEF2F2),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFFECACA), width: 1.5),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.cancel_rounded, color: AppColors.error),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Permohonan Ditolak',
                  style: AppTypography.labelBold.copyWith(color: AppColors.error),
                ),
                const SizedBox(height: 2),
                Text(
                  'Alasan: $alasan',
                  style: AppTypography.caption.copyWith(color: const Color(0xFF991B1B)),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAttachmentPreviewBox({required String? lampiran}) {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Berkas Lampiran Pendukung',
            style: AppTypography.labelBold.copyWith(
              color: AppColors.textPrimary,
              fontSize: 14,
            ),
          ),
          const SizedBox(height: AppSpacing.sm),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: const Color(0xFFF8FAFC),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFFE2E8F0)),
            ),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: AppColors.secondary,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(
                    Icons.file_present_rounded,
                    color: AppColors.primaryAccent,
                    size: 22,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        lampiran != null
                            ? lampiran.split('/').last
                            : 'Dokumen_KTP_KK_Pemohon.pdf',
                        style: AppTypography.labelBold.copyWith(fontSize: 13),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      Text(
                        'Lampiran Terverifikasi • 1.2 MB',
                        style: AppTypography.caption.copyWith(
                          color: AppColors.textSecondary,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ),
                const Icon(
                  Icons.open_in_new_rounded,
                  size: 18,
                  color: AppColors.primaryAccent,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLetterheadPaperPreview({
    required String namaSurat,
    required String nomorResmi,
    required String namaWarga,
    required String nik,
    required String alamat,
    required String keperluan,
    required String? drafAi,
    required String status,
    required String metode,
  }) {
    final isDone = status == 'selesai' || status == 'disetujui';

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFCBD5E1)),
        boxShadow: const [
          BoxShadow(
            color: Color(0x12000000),
            blurRadius: 16,
            offset: Offset(0, 6),
          ),
        ],
      ),
      padding: const EdgeInsets.all(AppSpacing.xl),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          // Kop Surat RT Formal
          Text(
            'RUKUN TETANGGA 04 / RUKUN WARGA 07',
            style: AppTypography.heading3.copyWith(
              fontWeight: FontWeight.w800,
              fontSize: 14,
              letterSpacing: 0.5,
            ),
            textAlign: TextAlign.center,
          ),
          Text(
            'KELURAHAN TAWANGSARI - KECAMATAN TAMAN',
            style: AppTypography.caption.copyWith(
              fontWeight: FontWeight.w700,
              fontSize: 11,
            ),
            textAlign: TextAlign.center,
          ),
          Text(
            'KABUPATEN SIDOARJO, JAWA TIMUR',
            style: AppTypography.caption.copyWith(
              fontWeight: FontWeight.w500,
              fontSize: 10,
              color: AppColors.textSecondary,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),

          // Double underline kop
          Container(height: 2, color: Colors.black87),
          const SizedBox(height: 2),
          Container(height: 0.8, color: Colors.black54),
          const SizedBox(height: AppSpacing.md),

          // Judul Surat & Nomor
          Text(
            namaSurat.toUpperCase(),
            style: AppTypography.heading3.copyWith(
              fontWeight: FontWeight.w800,
              fontSize: 15,
              decoration: TextDecoration.underline,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 2),
          Text(
            'Nomor: $nomorResmi',
            style: AppTypography.caption.copyWith(fontWeight: FontWeight.w600),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: AppSpacing.lg),

          // Body Text
          Align(
            alignment: Alignment.centerLeft,
            child: Text(
              'Yang bertanda tangan di bawah ini Ketua Rukun Tetangga 04 RW 07 Kelurahan Tawangsari, dengan ini menerangkan bahwa:',
              style: AppTypography.caption.copyWith(height: 1.4),
            ),
          ),
          const SizedBox(height: AppSpacing.sm),

          // Table / Citizen Details
          _buildPaperFieldRow('Nama Lengkap', ': $namaWarga'),
          _buildPaperFieldRow('NIK', ': $nik'),
          _buildPaperFieldRow('Alamat Domisili', ': $alamat'),
          _buildPaperFieldRow('Keperluan', ': $keperluan'),
          const SizedBox(height: AppSpacing.sm),

          Align(
            alignment: Alignment.centerLeft,
            child: Text(
              drafAi ??
                  'Orang tersebut di atas adalah benar-benar warga kami yang bertempat tinggal di lingkungan RT 04 RW 07 dan berkelakuan baik. Surat pengantar ini dibuat untuk dipergunakan sebagaimana mestinya.',
              style: AppTypography.caption.copyWith(height: 1.4),
            ),
          ),
          const SizedBox(height: AppSpacing.xl),

          // Signature Block
          Align(
            alignment: Alignment.centerRight,
            child: SizedBox(
              width: 180,
              child: Column(
                children: [
                  Text('Tawangsari, 2024', style: AppTypography.caption),
                  Text(
                    'Ketua RT 04 / RW 07',
                    style: AppTypography.caption.copyWith(fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 12),

                  // Digital Seal / QR / Physical Stamp Placeholder
                  Container(
                    width: 90,
                    height: 70,
                    decoration: BoxDecoration(
                      color: isDone ? const Color(0xFFEFF6FF) : const Color(0xFFF1F5F9),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(
                        color: isDone ? const Color(0xFF2563EB) : const Color(0xFFCBD5E1),
                        style: isDone ? BorderStyle.solid : BorderStyle.none,
                      ),
                    ),
                    child: Center(
                      child: isDone
                          ? Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                const Icon(Icons.qr_code_2_rounded, color: Color(0xFF2563EB), size: 36),
                                Text(
                                  'TERVERIFIKASI',
                                  style: AppTypography.caption.copyWith(
                                    fontSize: 8,
                                    fontWeight: FontWeight.w800,
                                    color: const Color(0xFF2563EB),
                                  ),
                                ),
                              ],
                            )
                          : Text(
                              '[ Draf Surat ]',
                              style: AppTypography.caption.copyWith(
                                color: AppColors.textMuted,
                                fontStyle: FontStyle.italic,
                              ),
                            ),
                    ),
                  ),
                  const SizedBox(height: 8),

                  Text(
                    '( Bambang Sutrisno )',
                    style: AppTypography.caption.copyWith(
                      fontWeight: FontWeight.w700,
                      decoration: TextDecoration.underline,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPaperFieldRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 110,
            child: Text(
              label,
              style: AppTypography.caption.copyWith(fontWeight: FontWeight.w500),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: AppTypography.caption.copyWith(fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStickyBottomBar(
    BuildContext context, {
    required bool isRT,
    required bool isPending,
    required bool isDone,
    required String metode,
    required String namaWarga,
    required String namaSurat,
  }) {
    // If User is RT and request is still pending
    if (isRT && isPending) {
      return Container(
        padding: const EdgeInsets.all(AppSpacing.md),
        decoration: const BoxDecoration(
          color: Colors.white,
          border: Border(top: BorderSide(color: AppColors.border)),
          boxShadow: [
            BoxShadow(
              color: Color(0x0A000000),
              blurRadius: 10,
              offset: Offset(0, -4),
            ),
          ],
        ),
        child: Row(
          children: [
            // Reject Button
            IconButton(
              icon: const Icon(Icons.cancel_outlined, color: AppColors.error),
              tooltip: 'Tolak Permohonan',
              onPressed: _showRTRejectDialog,
            ),
            const SizedBox(width: 4),

            // Revision Button
            IconButton(
              icon: const Icon(Icons.edit_note, color: Color(0xFFEA580C)),
              tooltip: 'Minta Revisi',
              onPressed: _showRTRevisionDialog,
            ),
            const SizedBox(width: 8),

            // Primary Approval & Signature Button
            Expanded(
              child: ElevatedButton.icon(
                onPressed: () async {
                  if (metode == 'digital') {
                    // Trigger Screen 11: PinAuthDialog
                    final success = await PinAuthDialog.show(
                      context,
                      namaWarga: namaWarga,
                      namaSurat: namaSurat,
                      onConfirm: (pin) async {
                        return await ref
                            .read(letterSubmitControllerProvider.notifier)
                            .signDigital(widget.applicationId, pin);
                      },
                    );
                    if (success == true && context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          backgroundColor: AppColors.success,
                          content: Text(
                            'Surat berhasil disahkan dengan PIN & tanda tangan digital!',
                          ),
                        ),
                      );
                      await context.push('/surat/preview/${widget.applicationId}');
                    }
                  } else {
                    await ref
                        .read(letterSubmitControllerProvider.notifier)
                        .confirmPhysical(widget.applicationId);
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          backgroundColor: AppColors.success,
                          content: Text('Surat fisik dikonfirmasi siap diambil warga.'),
                        ),
                      );
                    }
                  }
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primaryAccent,
                  foregroundColor: Colors.white,
                  elevation: 2,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                icon: Icon(
                  metode == 'digital' ? Icons.draw_rounded : Icons.check_circle_outline,
                  size: 20,
                  color: Colors.white,
                ),
                label: Text(
                  metode == 'digital' ? 'Setujui & Sahkan TTD' : 'Konfirmasi Siap Diambil',
                  style: AppTypography.labelBold.copyWith(
                    color: Colors.white,
                    fontSize: 13,
                  ),
                ),
              ),
            ),
          ],
        ),
      );
    }

    // If Document is Done (either for Warga or RT)
    if (isDone) {
      return Container(
        padding: const EdgeInsets.all(AppSpacing.md),
        decoration: const BoxDecoration(
          color: Colors.white,
          border: Border(top: BorderSide(color: AppColors.border)),
        ),
        child: RTPrimaryButton(
          text: 'Lihat & Unduh Dokumen PDF Resmi',
          icon: Icons.picture_as_pdf_rounded,
          onPressed: () => context.push('/surat/preview/${widget.applicationId}'),
        ),
      );
    }

    return const SizedBox.shrink();
  }
}
