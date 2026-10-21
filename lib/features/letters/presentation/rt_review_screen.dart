import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/router/route_names.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_typography.dart';
import '../../../shared/widgets/rt_status_badge.dart';
import 'letter_controller.dart';

/// Screen 9: Pengajuan Warga - Ketua RT (Figma Node #68:2321)
class RTReviewScreen extends ConsumerStatefulWidget {
  final int? selectedApplicationId;

  const RTReviewScreen({super.key, this.selectedApplicationId});

  @override
  ConsumerState<RTReviewScreen> createState() => _RTReviewScreenState();
}

class _RTReviewScreenState extends ConsumerState<RTReviewScreen> {
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
    final queueAsync = ref.watch(incomingQueueProvider);

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: Text(
          'Antrean Pengajuan Warga',
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
          onPressed: () => context.go(RouteNames.rtHome),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: AppColors.primaryAccent),
            tooltip: 'Segarkan Data',
            onPressed: () => ref.refresh(incomingQueueProvider),
          ),
        ],
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
                      onChanged: (val) =>
                          setState(() => _searchQuery = val.toLowerCase()),
                      style: AppTypography.bodySmall,
                      decoration: const InputDecoration(
                        hintText: 'Cari nama warga, nomor, atau surat...',
                        hintStyle: TextStyle(
                          color: Color(0xFF94A3B8),
                          fontSize: 13,
                        ),
                        prefixIcon: Icon(
                          Icons.search,
                          color: Color(0xFF64748B),
                          size: 20,
                        ),
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
                        _buildFilterChip('Perlu Review', 'diajukan'),
                        _buildFilterChip('Perlu Revisi', 'perlu revisi', isAlert: true),
                        _buildFilterChip('Disetujui', 'disetujui'),
                        _buildFilterChip('Selesai', 'selesai'),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const Divider(height: 1, color: AppColors.border),

            // Queue List
            Expanded(
              child: queueAsync.when(
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (err, _) => Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(
                        Icons.error_outline,
                        size: 48,
                        color: AppColors.error,
                      ),
                      const SizedBox(height: AppSpacing.sm),
                      Text('Gagal memuat antrean: $err',
                          style: AppTypography.bodySmall),
                      TextButton(
                        onPressed: () => ref.refresh(incomingQueueProvider),
                        child: const Text('Muat Ulang'),
                      ),
                    ],
                  ),
                ),
                data: (queue) {
                  final filtered = queue.where((item) {
                    final status =
                        item['status']?.toString().toLowerCase() ?? '';
                    final namaWarga =
                        item['nama_lengkap']?.toString().toLowerCase() ?? '';
                    final namaSurat =
                        item['nama_surat']?.toString().toLowerCase() ?? '';
                    final nomor =
                        item['nomor_pengajuan']?.toString().toLowerCase() ?? '';

                    final matchesFilter = _selectedFilter == 'semua' ||
                        status == _selectedFilter ||
                        (_selectedFilter == 'diajukan' &&
                            (status == 'diajukan' || status == 'diproses')) ||
                        (_selectedFilter == 'perlu revisi' &&
                            status.contains('revisi'));

                    final matchesSearch = _searchQuery.isEmpty ||
                        namaWarga.contains(_searchQuery) ||
                        namaSurat.contains(_searchQuery) ||
                        nomor.contains(_searchQuery);

                    return matchesFilter && matchesSearch;
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
                                Icons.checklist_rounded,
                                size: 32,
                                color: AppColors.textMuted,
                              ),
                            ),
                            const SizedBox(height: AppSpacing.md),
                            Text(
                              'Tidak ada antrean surat',
                              style: AppTypography.heading3.copyWith(
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              _searchQuery.isNotEmpty
                                  ? 'Tidak ada permohonan yang sesuai dengan filter pencarian.'
                                  : 'Seluruh permohonan warga telah ditinjau dan diselesaikan.',
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
                    onRefresh: () async => ref.refresh(incomingQueueProvider),
                    child: ListView.separated(
                      padding: const EdgeInsets.all(AppSpacing.lg),
                      itemCount: filtered.length,
                      separatorBuilder: (_, __) =>
                          const SizedBox(height: AppSpacing.md),
                      itemBuilder: (context, index) {
                        final item = filtered[index];
                        final id = item['pengajuan_id'] as int? ?? 0;
                        final nomorPengajuan =
                            item['nomor_pengajuan']?.toString() ?? '-';
                        final namaSurat =
                            item['nama_surat']?.toString() ?? 'Surat Pengantar';
                        final namaWarga =
                            item['nama_lengkap']?.toString() ??
                            item['nama_warga']?.toString() ??
                            'Warga';
                        final alamat = item['alamat']?.toString() ?? '-';
                        final keperluan = item['keperluan']?.toString() ?? '-';
                        final status =
                            item['status']?.toString().toLowerCase() ?? 'diajukan';
                        final metode =
                            item['metode_tanda_tangan']?.toString() ?? 'digital';

                        return _buildReviewFeedCard(
                          context,
                          id: id,
                          nomorPengajuan: nomorPengajuan,
                          namaSurat: namaSurat,
                          namaWarga: namaWarga,
                          alamat: alamat,
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

  Widget _buildReviewFeedCard(
    BuildContext context, {
    required int id,
    required String nomorPengajuan,
    required String namaSurat,
    required String namaWarga,
    required String alamat,
    required String keperluan,
    required String status,
    required String metode,
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

    // Accent left border color based on status
    Color accentColor = AppColors.primaryAccent;
    if (status == 'perlu revisi' || status == 'perlu_revisi') {
      accentColor = const Color(0xFFD97706);
    } else if (status == 'selesai' || status == 'disetujui') {
      accentColor = const Color(0xFF10B981);
    } else if (status == 'ditolak') {
      accentColor = AppColors.error;
    }

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
      child: ClipRRect(
        borderRadius: BorderRadius.circular(16),
        child: IntrinsicHeight(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Accent status line
              Container(width: 5, color: accentColor),
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.all(AppSpacing.md),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Header Row
                      Row(
                        children: [
                          CircleAvatar(
                            radius: 18,
                            backgroundColor: const Color(0xFFEFF6FF),
                            child: Text(
                              initials,
                              style: AppTypography.labelBold.copyWith(
                                color: AppColors.primaryAccent,
                                fontSize: 12,
                              ),
                            ),
                          ),
                          const SizedBox(width: AppSpacing.sm),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  namaWarga,
                                  style: AppTypography.labelBold.copyWith(
                                    fontSize: 14,
                                  ),
                                ),
                                Text(
                                  alamat,
                                  style: AppTypography.caption.copyWith(
                                    color: AppColors.textSecondary,
                                    fontSize: 11,
                                  ),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
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

                      // Document Type & Purpose
                      Text(
                        namaSurat,
                        style: AppTypography.heading3.copyWith(
                          fontWeight: FontWeight.w700,
                          fontSize: 15,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        keperluan,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: AppTypography.bodySmall.copyWith(
                          color: AppColors.textSecondary,
                          fontSize: 12,
                        ),
                      ),
                      const SizedBox(height: AppSpacing.md),

                      // Method and CTA
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 3,
                            ),
                            decoration: BoxDecoration(
                              color: const Color(0xFFF1F5F9),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Row(
                              children: [
                                Icon(
                                  metode == 'digital'
                                      ? Icons.qr_code_2_rounded
                                      : Icons.edit_note_rounded,
                                  size: 14,
                                  color: const Color(0xFF475569),
                                ),
                                const SizedBox(width: 4),
                                Text(
                                  metode == 'digital'
                                      ? 'TTD Digital'
                                      : 'TTD Basah',
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
                          ElevatedButton.icon(
                            onPressed: () => context.push('/letters/$id'),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppColors.primaryAccent,
                              foregroundColor: Colors.white,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(10),
                              ),
                              padding: const EdgeInsets.symmetric(
                                horizontal: 14,
                                vertical: 8,
                              ),
                              elevation: 0,
                            ),
                            icon: const Icon(
                              Icons.visibility_outlined,
                              size: 16,
                            ),
                            label: Text(
                              'Periksa Detail',
                              style: AppTypography.labelBold.copyWith(
                                color: Colors.white,
                                fontSize: 12,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
