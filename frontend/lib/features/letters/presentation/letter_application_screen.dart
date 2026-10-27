import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_picker/file_picker.dart';
import 'package:go_router/go_router.dart';
import '../../../core/router/route_names.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_typography.dart';
import '../../../shared/widgets/rt_primary_button.dart';
import '../../../shared/widgets/rt_text_field.dart';
import 'letter_controller.dart';

/// Screen 7: Formulir Pengajuan Warga (Figma Node #68:2607)
class LetterApplicationScreen extends ConsumerStatefulWidget {
  const LetterApplicationScreen({super.key});

  @override
  ConsumerState<LetterApplicationScreen> createState() =>
      _LetterApplicationScreenState();
}

class _LetterApplicationScreenState
    extends ConsumerState<LetterApplicationScreen> {
  final _formKey = GlobalKey<FormState>();
  final _keperluanController = TextEditingController();

  int? _selectedJenisSuratId;
  String? _selectedSyarat;
  String _metodeTtd = 'digital'; // 'digital' or 'basah'
  String? _lampiranPath;
  String? _lampiranFileName;

  @override
  void dispose() {
    _keperluanController.dispose();
    super.dispose();
  }

  Future<void> _pickAttachment() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf', 'png', 'jpg', 'jpeg'],
    );
    if (result != null && result.files.single.path != null) {
      setState(() {
        _lampiranPath = result.files.single.path;
        _lampiranFileName = result.files.single.name;
      });
    }
  }

  void _removeAttachment() {
    setState(() {
      _lampiranPath = null;
      _lampiranFileName = null;
    });
  }

  Future<void> _submitApplication() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedJenisSuratId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          backgroundColor: AppColors.error,
          content: Text('Silakan pilih jenis surat terlebih dahulu'),
        ),
      );
      return;
    }

    final success = await ref
        .read(letterSubmitControllerProvider.notifier)
        .submitApplication(
          jenisSuratId: _selectedJenisSuratId!,
          keperluan: _keperluanController.text.trim(),
          metodeTandaTangan: _metodeTtd,
          lampiranPath: _lampiranPath,
        );

    if (mounted) {
      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            backgroundColor: AppColors.success,
            content: Text(
              'Permohonan surat berhasil dikirim! Draf surat otomatis telah disiapkan untuk ditinjau.',
            ),
          ),
        );
        context.go(RouteNames.wargaPengajuan);
      } else {
        final error =
            ref.read(letterSubmitControllerProvider).errorMessage ??
            'Gagal mengirim permohonan';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            backgroundColor: AppColors.error,
            content: Text(error),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final letterTypesAsync = ref.watch(letterTypesProvider);
    final submitState = ref.watch(letterSubmitControllerProvider);

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: Text(
          'Pengajuan Surat',
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
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSpacing.lg),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Info Banner (Figma #68:2607)
                Container(
                  padding: const EdgeInsets.all(AppSpacing.md),
                  decoration: BoxDecoration(
                    color: const Color(0xFFEFF6FF),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: const Color(0xFFBFDBFE)),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: const Color(0xFFDBEAFE),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: const Icon(
                          Icons.verified_user_rounded,
                          color: AppColors.primaryAccent,
                          size: 22,
                        ),
                      ),
                      const SizedBox(width: AppSpacing.md),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Data Diri Otomatis Diisi',
                              style: AppTypography.labelBold.copyWith(
                                color: const Color(0xFF1E40AF),
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              'NIK, Nama, dan Alamat Anda akan otomatis disematkan ke dalam format resmi surat pengantar RT.',
                              style: AppTypography.caption.copyWith(
                                color: const Color(0xFF1E3A8A),
                                height: 1.3,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: AppSpacing.xl),

                // Section 1: Pilih Jenis Surat
                Text(
                  'Jenis Surat Pengantar',
                  style: AppTypography.labelBold.copyWith(
                    color: AppColors.textPrimary,
                    fontSize: 14,
                  ),
                ),
                const SizedBox(height: AppSpacing.xs),
                letterTypesAsync.when(
                  loading: () => Container(
                    height: 52,
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppColors.border),
                    ),
                    child: const Center(
                      child: SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                    ),
                  ),
                  error: (err, _) => Text(
                    'Gagal memuat jenis surat: $err',
                    style: const TextStyle(color: AppColors.error),
                  ),
                  data: (types) {
                    return Container(
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: AppColors.border),
                      ),
                      child: DropdownButtonFormField<int>(
                        initialValue: _selectedJenisSuratId,
                        dropdownColor: Colors.white,
                        decoration: const InputDecoration(
                          hintText: 'Pilih jenis surat yang diajukan...',
                          hintStyle: TextStyle(
                            color: AppColors.textMuted,
                            fontSize: 14,
                          ),
                          border: InputBorder.none,
                          contentPadding: EdgeInsets.symmetric(
                            horizontal: 16,
                            vertical: 14,
                          ),
                        ),
                        icon: const Icon(
                          Icons.keyboard_arrow_down_rounded,
                          color: AppColors.textSecondary,
                        ),
                        items: types.map((t) {
                          return DropdownMenuItem<int>(
                            value: t['jenis_surat_id'] as int,
                            child: Text(
                              t['nama_surat'].toString(),
                              style: AppTypography.bodySmall.copyWith(
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          );
                        }).toList(),
                        onChanged: (val) {
                          setState(() {
                            _selectedJenisSuratId = val;
                            final match = types.firstWhere(
                              (e) => e['jenis_surat_id'] == val,
                            );
                            _selectedSyarat =
                                match['persyaratan_dokumen']?.toString();
                          });
                        },
                        validator: (val) =>
                            val == null ? 'Wajib memilih jenis surat' : null,
                      ),
                    );
                  },
                ),

                // Persyaratan Berkas Callout
                if (_selectedSyarat != null) ...[
                  const SizedBox(height: AppSpacing.sm),
                  Container(
                    padding: const EdgeInsets.all(AppSpacing.md),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF8FAFC),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0xFFE2E8F0)),
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(
                          Icons.assignment_turned_in_outlined,
                          color: Color(0xFF475569),
                          size: 18,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Persyaratan Berkas:',
                                style: AppTypography.labelBold.copyWith(
                                  fontSize: 12,
                                  color: const Color(0xFF334155),
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                _selectedSyarat!,
                                style: AppTypography.caption.copyWith(
                                  color: const Color(0xFF475569),
                                  height: 1.3,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
                const SizedBox(height: AppSpacing.lg),

                // Section 2: Keperluan / Alasan
                RTTextField(
                  label: 'Keperluan / Alasan Pengajuan',
                  hint:
                      'Contoh: Pengurusan Surat Keterangan Catatan Kepolisian (SKCK) untuk melamar pekerjaan di instansi BUMN.',
                  controller: _keperluanController,
                  maxLines: 4,
                  isRequired: true,
                  helperText: 'Jelaskan keperluan pengajuan dengan jelas dan rinci.',
                  validator: (v) => (v == null || v.trim().length < 5)
                      ? 'Mohon jelaskan keperluan minimal 5 karakter'
                      : null,
                ),
                const SizedBox(height: AppSpacing.lg),

                // Section 3: Pilihan Metode Tanda Tangan (Radio Cards)
                Text(
                  'Metode Pengesahan Tanda Tangan',
                  style: AppTypography.labelBold.copyWith(
                    color: AppColors.textPrimary,
                    fontSize: 14,
                  ),
                ),
                const SizedBox(height: AppSpacing.xs),
                _buildSignatureOptionCard(
                  title: 'Tanda Tangan Digital (Rekomendasi)',
                  badge: 'Cepat & Praktis',
                  subtitle:
                      'Surat disahkan langsung secara digital dengan tanda tangan resmi Ketua RT. Dapat langsung diunduh dalam format PDF.',
                  value: 'digital',
                  icon: Icons.qr_code_2_rounded,
                ),
                const SizedBox(height: AppSpacing.sm),
                _buildSignatureOptionCard(
                  title: 'Tanda Tangan Basah (Fisik)',
                  badge: null,
                  subtitle:
                      'Surat fisik dicetak dan ditandatangani manual oleh Ketua RT. Warga mengambil surat langsung di kediaman RT.',
                  value: 'basah',
                  icon: Icons.edit_note_rounded,
                ),
                const SizedBox(height: AppSpacing.lg),

                // Section 4: Berkas Lampiran Pendukung
                Text(
                  'Berkas Lampiran Pendukung (Opsional)',
                  style: AppTypography.labelBold.copyWith(
                    color: AppColors.textPrimary,
                    fontSize: 14,
                  ),
                ),
                const SizedBox(height: AppSpacing.xs),
                _buildAttachmentSection(),
                const SizedBox(height: AppSpacing.xl),

                // Section 5: Submit Button
                RTPrimaryButton(
                  text: 'Kirim Pengajuan Surat',
                  isLoading: submitState.isLoading,
                  icon: Icons.send_rounded,
                  onPressed: _submitApplication,
                ),
                const SizedBox(height: 40),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildSignatureOptionCard({
    required String title,
    required String? badge,
    required String subtitle,
    required String value,
    required IconData icon,
  }) {
    final isSelected = _metodeTtd == value;

    return InkWell(
      onTap: () => setState(() => _metodeTtd = value),
      borderRadius: BorderRadius.circular(16),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.all(AppSpacing.md),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFFEFF6FF) : Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isSelected ? AppColors.primaryAccent : AppColors.border,
            width: isSelected ? 2.0 : 1.0,
          ),
          boxShadow: [
            if (isSelected)
              BoxShadow(
                color: AppColors.primaryAccent.withValues(alpha: 0.1),
                blurRadius: 8,
                offset: const Offset(0, 3),
              ),
          ],
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 38,
              height: 38,
              decoration: BoxDecoration(
                color: isSelected
                    ? AppColors.primaryAccent
                    : const Color(0xFFF1F5F9),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(
                icon,
                color: isSelected ? Colors.white : AppColors.textSecondary,
                size: 22,
              ),
            ),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(
                        title,
                        style: AppTypography.labelBold.copyWith(
                          color: isSelected
                              ? AppColors.primaryAccent
                              : AppColors.textPrimary,
                          fontSize: 14,
                        ),
                      ),
                      if (badge != null) ...[
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 6,
                            vertical: 2,
                          ),
                          decoration: BoxDecoration(
                            color: const Color(0xFFDCFCE7),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            badge,
                            style: AppTypography.caption.copyWith(
                              color: const Color(0xFF15803D),
                              fontWeight: FontWeight.w700,
                              fontSize: 10,
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    subtitle,
                    style: AppTypography.caption.copyWith(
                      color: AppColors.textSecondary,
                      height: 1.3,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            Container(
              width: 22,
              height: 22,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: isSelected ? AppColors.primaryAccent : Colors.transparent,
                border: Border.all(
                  color: isSelected ? AppColors.primaryAccent : AppColors.border,
                  width: 2,
                ),
              ),
              child: isSelected
                  ? const Icon(Icons.check, size: 14, color: Colors.white)
                  : null,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAttachmentSection() {
    if (_lampiranFileName != null) {
      return Container(
        padding: const EdgeInsets.all(AppSpacing.md),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.primaryAccent),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: AppColors.secondary,
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(
                Icons.file_present_rounded,
                color: AppColors.primaryAccent,
                size: 24,
              ),
            ),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _lampiranFileName!,
                    style: AppTypography.labelBold.copyWith(fontSize: 13),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    'Lampiran terpilih',
                    style: AppTypography.caption.copyWith(
                      color: AppColors.success,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
            IconButton(
              icon: const Icon(Icons.close_rounded, color: AppColors.error),
              onPressed: _removeAttachment,
            ),
          ],
        ),
      );
    }

    return InkWell(
      onTap: _pickAttachment,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.lg,
          vertical: AppSpacing.xl,
        ),
        decoration: BoxDecoration(
          color: const Color(0xFFF8FAFC),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: const Color(0xFFCBD5E1),
            width: 1.5,
          ),
        ),
        child: Column(
          children: [
            Container(
              width: 48,
              height: 48,
              decoration: const BoxDecoration(
                color: Color(0xFFEDF0FF),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.cloud_upload_outlined,
                color: AppColors.primaryAccent,
                size: 26,
              ),
            ),
            const SizedBox(height: AppSpacing.sm),
            Text(
              'Klik untuk pilih berkas atau foto',
              style: AppTypography.labelBold.copyWith(
                color: AppColors.textPrimary,
                fontSize: 13,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              'Format PDF, PNG, atau JPG (Maks. 5 MB)',
              style: AppTypography.caption.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
