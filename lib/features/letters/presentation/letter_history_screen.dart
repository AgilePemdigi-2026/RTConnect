import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/router/route_names.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_typography.dart';
import '../../../shared/widgets/rt_bottom_nav_bar.dart';
import '../../../shared/widgets/rt_status_badge.dart';
import 'letter_controller.dart';

/// Screen 6: Riwayat Pengajuan Warga (Figma Node #68:2794)
class LetterHistoryScreen extends ConsumerStatefulWidget {
  const LetterHistoryScreen({super.key});

  @override
  ConsumerState<LetterHistoryScreen> createState() =>
      _LetterHistoryScreenState();
}

class _LetterHistoryScreenState extends ConsumerState<LetterHistoryScreen> {
  String _selectedFilter = 'semua';
  final TextEditingController _searchController = TextEditingController();
  String _searchQuery = '';

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final applicationsAsync = ref.watch(myApplicationsProvider);

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: Text(
          'Riwayat Pengajuan',
          style: AppTypography.heading3.copyWith(
            color: AppColors.textPrimary,
            fontWeight: FontWeight.w800,
          ),
        ),
        centerTitle: false,
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: AppColors.textPrimary, size: 20),
          onPressed: () => context.go(RouteNames.wargaHome),
        ),
        bottom: const PreferredSize(
          preferredSize: Size.fromHeight(1.0),
          child: Divider(height: 1.0, color: AppColors.border),
        ),
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Search Bar & Filter Header
            Container(
              color: Colors.white,
              padding: const EdgeInsets.fromLTRB(
                AppSpacing.lg,
                AppSpacing.md,
                AppSpacing.lg,
                AppSpacing.sm,
              ),
              child: Column(
                children: [
                  // Search Box
                  Container(
                    height: 44,
                    decoration: BoxDecoration(
                      color: const Color(0xFFF1F5F9),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0xFFE2E8F0)),
                    ),
                    child: TextField(
                      controller: _searchController,
                      onChanged: (val) => setState(() => _searchQuery = val.toLowerCase()),
                      style: AppTypography.bodySmall,
                      decoration: const InputDecoration(
                        hintText: 'Cari surat pengantar atau nomor...',
                        hintStyle: TextStyle(color: Color(0xFF94A3B8), fontSize: 13),
                        prefixIcon: Icon(Icons.search, color: Color(0xFF64748B), size: 20),
                        border: InputBorder.none,
                        contentPadding: EdgeInsets.symmetric(vertical: 10),
                      ),
                    ),
                  ),
                  const SizedBox(height: AppSpacing.sm),

                  // Horizontal Filter Chips
                  SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: [
                        _buildFilterChip('Semua', 'semua'),
                        _buildFilterChip('Perlu Revisi', 'perlu revisi', isAlert: true),
                        _buildFilterChip('Diajukan', 'diajukan'),
                        _buildFilterChip('Diproses', 'diproses'),
                        _buildFilterChip('Selesai', 'selesai'),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const Divider(height: 1, color: AppColors.border),

            // Daftar Pengajuan Feed
            Expanded(
              child: applicationsAsync.when(
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (err, _) => Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline, size: 48, color: AppColors.error),
                      const SizedBox(height: AppSpacing.sm),
                      Text('Gagal memuat data surat: $err', style: AppTypography.bodySmall),
                      TextButton(
                        onPressed: () => ref.refresh(myApplicationsProvider),
                        child: const Text('Coba Lagi'),
                      ),
                    ],
                  ),
                ),
                data: (apps) {
                  final filtered = apps.where((a) {
                    final status = a['status']?.toString().toLowerCase() ?? '';
                    final namaSurat = a['nama_surat']?.toString().toLowerCase() ?? '';
                    final nomor = a['nomor_pengajuan']?.toString().toLowerCase() ?? '';

                    // Status filter
                    final matchesStatus = _selectedFilter == 'semua' ||
                        status == _selectedFilter ||
                        (_selectedFilter == 'perlu revisi' && status.contains('revisi'));

                    // Search query filter
                    final matchesSearch = _searchQuery.isEmpty ||
                        namaSurat.contains(_searchQuery) ||
                        nomor.contains(_searchQuery);

                    return matchesStatus && matchesSearch;
                  }).toList();

                  if (filtered.isEmpty) {
                    return Center(
                      child: Padding(
                        padding: const EdgeInsets.all(AppSpacing.xl),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Container(
                              width: 64,
                              height: 64,
                              decoration: const BoxDecoration(
                                color: Color(0xFFF1F5F9),
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(
                                Icons.inbox_outlined,
                                size: 32,
                                color: AppColors.textMuted,
                              ),
                            ),
                            const SizedBox(height: AppSpacing.md),
                            Text(
                              'Tidak ada pengajuan ditemukan',
                              style: AppTypography.heading3.copyWith(
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              _searchQuery.isNotEmpty
                                  ? 'Tidak ada permohonan yang sesuai dengan pencarian Anda.'
                                  : 'Pengajuan surat yang Anda buat akan muncul di daftar ini.',
                              style: AppTypography.caption.copyWith(
                                color: AppColors.textSecondary,
                              ),
                              textAlign: TextAlign.center,
                            ),
                          ],
                        ),
                      ),
                    );
                  }

                  return RefreshIndicator(
                    onRefresh: () async => ref.refresh(myApplicationsProvider),
                    child: ListView.separated(
                      padding: const EdgeInsets.fromLTRB(
                        AppSpacing.lg,
                        AppSpacing.md,
                        AppSpacing.lg,
                        80,
                      ),
                      itemCount: filtered.length,
                      separatorBuilder: (_, __) => const SizedBox(height: AppSpacing.md),
                      itemBuilder: (context, index) {
                        final item = filtered[index];
                        final id = item['pengajuan_id'] as int? ?? 0;
                        final nomorPengajuan = item['nomor_pengajuan']?.toString() ?? '-';
                        final namaSurat = item['nama_surat']?.toString() ?? 'Surat Pengantar';
                        final keperluan = item['keperluan']?.toString() ?? '-';
                        final status = item['status']?.toString().toLowerCase() ?? 'diajukan';
                        final metode = item['metode_tanda_tangan']?.toString() ?? 'digital';
                        final catatan = item['catatan']?.toString();

                        final isRevision = status == 'perlu revisi' || status == 'perlu_revisi';

                        if (isRevision) {
                          return _buildRevisionCard(
                            context,
                            id: id,
                            nomorPengajuan: nomorPengajuan,
                            namaSurat: namaSurat,
                            keperluan: keperluan,
                            status: status,
                            catatan: catatan ?? 'Mohon periksa kembali dokumen lampiran sesuai catatan RT.',
                          );
                        }

                        return _buildStandardCard(
                          context,
                          id: id,
                          nomorPengajuan: nomorPengajuan,
                          namaSurat: namaSurat,
                          keperluan: keperluan,
                          status: status,
                          metode: metode,
                        );
                      },
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: RTBottomNavBar(
        currentIndex: 1,
        onTap: (index) {
          if (index == 1) return;
          if (index == 0) {
            context.go(RouteNames.wargaHome);
          } else if (index == 2) {
            context.push(RouteNames.chatbot);
          }
        },
      ),
      floatingActionButton: Padding(
        padding: const EdgeInsets.only(bottom: 60.0),
        child: SizedBox(
          height: 52,
          child: ElevatedButton.icon(
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primaryAccent,
              foregroundColor: Colors.white,
              elevation: 4,
              shadowColor: AppColors.primaryAccent.withValues(alpha: 0.4),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
              padding: const EdgeInsets.symmetric(horizontal: 20),
            ),
            onPressed: () => context.push(RouteNames.wargaPengajuanBaru),
            icon: const Icon(Icons.add, size: 20),
            label: Text(
              'Buat Pengajuan Baru',
              style: AppTypography.labelBold.copyWith(
                color: Colors.white,
                fontSize: 14,
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildFilterChip(String label, String value, {bool isAlert = false}) {
    final isSelected = _selectedFilter == value;

    return Padding(
      padding: const EdgeInsets.only(right: 8.0),
      child: InkWell(
        onTap: () => setState(() => _selectedFilter = value),
        borderRadius: BorderRadius.circular(9999),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
          decoration: BoxDecoration(
            color: isSelected
                ? (isAlert ? AppColors.error : AppColors.primaryAccent)
                : const Color(0xFFF1F5F9),
            borderRadius: BorderRadius.circular(9999),
            border: Border.all(
              color: isSelected
                  ? (isAlert ? AppColors.error : AppColors.primaryAccent)
                  : const Color(0xFFE2E8F0),
            ),
          ),
          child: Text(
            label,
            style: AppTypography.caption.copyWith(
              color: isSelected ? Colors.white : const Color(0xFF475569),
              fontWeight: isSelected ? FontWeight.w700 : FontWeight.w600,
              fontSize: 12,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildStandardCard(
    BuildContext context, {
    required int id,
    required String nomorPengajuan,
    required String namaSurat,
    required String keperluan,
    required String status,
    required String metode,
  }) {
    return Container(
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
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () => context.push('/letters/$id'),
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.md),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      nomorPengajuan,
                      style: AppTypography.caption.copyWith(
                        fontWeight: FontWeight.w700,
                        color: AppColors.textSecondary,
                      ),
                    ),
                    RTStatusBadge(status: status),
                  ],
                ),
                const SizedBox(height: 6),
                Text(
                  namaSurat,
                  style: AppTypography.heading3.copyWith(
                    fontWeight: FontWeight.w700,
                    fontSize: 16,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  keperluan,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: AppTypography.bodySmall.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
                const SizedBox(height: AppSpacing.md),
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: const Color(0xFFF1F5F9),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Row(
                        children: [
                          Icon(
                            metode == 'digital' ? Icons.qr_code : Icons.edit_note,
                            size: 14,
                            color: const Color(0xFF475569),
                          ),
                          const SizedBox(width: 4),
                          Text(
                            metode == 'digital' ? 'TTD Digital' : 'TTD Basah',
                            style: AppTypography.caption.copyWith(
                              color: const Color(0xFF475569),
                              fontWeight: FontWeight.w600,
                              fontSize: 11,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const Spacer(),
                    Text(
                      'Lihat Detail',
                      style: AppTypography.caption.copyWith(
                        color: AppColors.primaryAccent,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(width: 2),
                    const Icon(
                      Icons.chevron_right_rounded,
                      size: 16,
                      color: AppColors.primaryAccent,
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildRevisionCard(
    BuildContext context, {
    required int id,
    required String nomorPengajuan,
    required String namaSurat,
    required String keperluan,
    required String status,
    required String catatan,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFFFFF7ED),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFFED7AA), width: 1.5),
        boxShadow: const [
          BoxShadow(
            color: Color(0x08BA1A1A),
            blurRadius: 10,
            offset: Offset(0, 4),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  nomorPengajuan,
                  style: AppTypography.caption.copyWith(
                    fontWeight: FontWeight.w700,
                    color: const Color(0xFF9A3412),
                  ),
                ),
                RTStatusBadge(status: status),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              namaSurat,
              style: AppTypography.heading3.copyWith(
                fontWeight: FontWeight.w700,
                fontSize: 16,
                color: const Color(0xFF7C2D12),
              ),
            ),
            const SizedBox(height: 4),
            Text(
              keperluan,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: AppTypography.bodySmall.copyWith(
                color: const Color(0xFF9A3412),
              ),
            ),
            const SizedBox(height: AppSpacing.md),

            // Quoted RT Note Banner (Figma #68:2794)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(AppSpacing.sm),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: const Color(0xFFFDBA74)),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(
                    Icons.rate_review_outlined,
                    color: Color(0xFFEA580C),
                    size: 18,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Catatan Perbaikan dari Ketua RT:',
                          style: AppTypography.caption.copyWith(
                            fontWeight: FontWeight.w700,
                            color: const Color(0xFFC2410C),
                            fontSize: 11,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          '"$catatan"',
                          style: AppTypography.caption.copyWith(
                            fontStyle: FontStyle.italic,
                            color: const Color(0xFF7C2D12),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.md),

            // Action Buttons
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: () => context.push('/letters/$id'),
                    style: OutlinedButton.styleFrom(
                      side: const BorderSide(color: Color(0xFFF97316)),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                      padding: const EdgeInsets.symmetric(vertical: 10),
                    ),
                    child: Text(
                      'Lihat Detail',
                      style: AppTypography.labelBold.copyWith(
                        color: const Color(0xFFEA580C),
                        fontSize: 12,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: ElevatedButton(
                    onPressed: () => context.push('/letters/$id'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFEA580C),
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                      padding: const EdgeInsets.symmetric(vertical: 10),
                    ),
                    child: Text(
                      'Perbaiki Data',
                      style: AppTypography.labelBold.copyWith(
                        color: Colors.white,
                        fontSize: 12,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
