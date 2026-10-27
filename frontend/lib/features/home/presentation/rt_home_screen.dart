import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/router/route_names.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_typography.dart';
import '../../../shared/widgets/rt_drawer_menu.dart';
import '../../../shared/widgets/rt_status_badge.dart';
import '../../auth/presentation/auth_controller.dart';
import '../../letters/presentation/letter_controller.dart';
import '../../notifications/presentation/notification_controller.dart';

/// Screen 8: Beranda RT (Figma Node #83:1362)
class RTHomeScreen extends ConsumerWidget {
  const RTHomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authControllerProvider);
    final user = authState.user;
    final queueAsync = ref.watch(incomingQueueProvider);
    final unreadNotifs = ref.watch(unreadNotificationCountProvider);

    final rtName = user?.namaLengkap ?? 'Pak Bambang';
    final initial = rtName.isNotEmpty ? rtName[0].toUpperCase() : 'B';

    return Scaffold(
      backgroundColor: AppColors.background,
      endDrawer: const RTDrawerMenu(),
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(64.0),
        child: Container(
          decoration: const BoxDecoration(
            color: Colors.white,
            border: Border(
              bottom: BorderSide(color: AppColors.border, width: 1.0),
            ),
          ),
          child: SafeArea(
            bottom: false,
            child: Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.lg,
                vertical: 8.0,
              ),
              child: Row(
                children: [
                  // App Brand + Badge
                  Row(
                    children: [
                      Container(
                        width: 34,
                        height: 34,
                        decoration: BoxDecoration(
                          color: AppColors.primary,
                          borderRadius: BorderRadius.circular(8.0),
                        ),
                        child: const Icon(
                          Icons.apartment_rounded,
                          color: Colors.white,
                          size: 20,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        'RTConnect',
                        style: AppTypography.heading3.copyWith(
                          color: AppColors.textPrimary,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      const SizedBox(width: 6),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 6,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFEF3C7),
                          borderRadius: BorderRadius.circular(4),
                          border: Border.all(color: const Color(0xFFFDE68A)),
                        ),
                        child: Text(
                          'KETUA RT',
                          style: AppTypography.caption.copyWith(
                            color: const Color(0xFFB45309),
                            fontWeight: FontWeight.w800,
                            fontSize: 10,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const Spacer(),

                  // Notifications
                  Stack(
                    children: [
                      IconButton(
                        icon: const Icon(
                          Icons.notifications_outlined,
                          color: AppColors.textPrimary,
                          size: 24,
                        ),
                        onPressed: () async {
                          await context.push(RouteNames.notifications);
                          ref.invalidate(notificationsProvider);
                        },
                      ),
                      if (unreadNotifs > 0)
                        Positioned(
                          top: 10,
                          right: 10,
                          child: Container(
                            width: 8,
                            height: 8,
                            decoration: const BoxDecoration(
                              color: AppColors.error,
                              shape: BoxShape.circle,
                            ),
                          ),
                        ),
                    ],
                  ),

                  // Profile Avatar triggering endDrawer
                  Builder(
                    builder: (scaffoldContext) {
                      return GestureDetector(
                        onTap: () =>
                            Scaffold.of(scaffoldContext).openEndDrawer(),
                        child: Container(
                          width: 38,
                          height: 38,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: const Color(0xFF0F172A),
                            border: Border.all(
                              color: AppColors.primaryAccent,
                              width: 2,
                            ),
                          ),
                          child: Center(
                            child: Text(
                              initial,
                              style: AppTypography.labelBold.copyWith(
                                color: Colors.white,
                              ),
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () async {
            ref.invalidate(incomingQueueProvider);
            ref.invalidate(notificationsProvider);
          },
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Location Pill
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: AppColors.secondary,
                    borderRadius: BorderRadius.circular(9999),
                    border: Border.all(color: const Color(0xFFBFDBFE)),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(
                        Icons.location_on,
                        size: 15,
                        color: AppColors.primary,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        '${AppConstants.rtArea} • Panel Pelayanan RT',
                        style: AppTypography.caption.copyWith(
                          color: AppColors.primary,
                          fontWeight: FontWeight.w600,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: AppSpacing.sm),

                // Greeting RT
                Text(
                  'Halo, $rtName 👋',
                  style: AppTypography.heading1.copyWith(
                    fontWeight: FontWeight.w800,
                    color: AppColors.textPrimary,
                    fontSize: 22,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Tinjau dan sahkan permohonan surat pengantar warga secara digital.',
                  style: AppTypography.bodySmall.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
                const SizedBox(height: AppSpacing.lg),

                // 3 Quick Metrics Cards (Figma #83:1362)
                queueAsync.when(
                  loading: () => Container(
                    height: 90,
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppColors.border),
                    ),
                    child: const Center(child: CircularProgressIndicator()),
                  ),
                  error: (e, _) => Text('Error: $e'),
                  data: (queue) {
                    final totalDiajukan = queue
                        .where((q) =>
                            q['status'] == 'diajukan' ||
                            q['status'] == 'diproses')
                        .length;
                    final totalRevisi = queue
                        .where((q) =>
                            q['status'] == 'perlu_revisi' ||
                            q['status'] == 'perlu revisi')
                        .length;
                    final totalSelesai = queue
                        .where((q) =>
                            q['status'] == 'selesai' ||
                            q['status'] == 'disetujui' ||
                            q['status'] == 'siap_diambil')
                        .length;

                    return Row(
                      children: [
                        Expanded(
                          child: _buildMetricCard(
                            title: 'Perlu Review',
                            count: totalDiajukan.toString(),
                            icon: Icons.pending_actions_rounded,
                            textColor: const Color(0xFF1D4ED8),
                            bgColor: const Color(0xFFEFF6FF),
                            borderColor: const Color(0xFFBFDBFE),
                          ),
                        ),
                        const SizedBox(width: AppSpacing.sm),
                        Expanded(
                          child: _buildMetricCard(
                            title: 'Perlu Revisi',
                            count: totalRevisi.toString(),
                            icon: Icons.edit_note_rounded,
                            textColor: const Color(0xFFD97706),
                            bgColor: const Color(0xFFFEF3C7),
                            borderColor: const Color(0xFFFDE68A),
                          ),
                        ),
                        const SizedBox(width: AppSpacing.sm),
                        Expanded(
                          child: _buildMetricCard(
                            title: 'Selesai',
                            count: totalSelesai.toString(),
                            icon: Icons.verified_rounded,
                            textColor: const Color(0xFF059669),
                            bgColor: const Color(0xFFECFDF5),
                            borderColor: const Color(0xFFA7F3D0),
                          ),
                        ),
                      ],
                    );
                  },
                ),
                const SizedBox(height: AppSpacing.xl),

                // Section Antrean Prioritas Peninjauan
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Antrean Masuk Terbaru',
                      style: AppTypography.heading3.copyWith(
                        fontWeight: FontWeight.w700,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    TextButton(
                      onPressed: () => context.push(RouteNames.rtQueue),
                      style: TextButton.styleFrom(
                        padding: EdgeInsets.zero,
                        minimumSize: Size.zero,
                        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      ),
                      child: Text(
                        'Buka Semua',
                        style: AppTypography.labelBold.copyWith(
                          color: AppColors.primaryAccent,
                          fontSize: 13,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: AppSpacing.md),

                // Recent Pending Cards Feed
                queueAsync.when(
                  loading: () => const Center(child: CircularProgressIndicator()),
                  error: (e, _) => Text('Error: $e'),
                  data: (queue) {
                    final pending = queue
                        .where((q) =>
                            q['status'] == 'diajukan' ||
                            q['status'] == 'diproses')
                        .toList();

                    if (pending.isEmpty) {
                      return Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(AppSpacing.xl),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: AppColors.border),
                        ),
                        child: Column(
                          children: [
                            const Icon(
                              Icons.task_alt_rounded,
                              size: 48,
                              color: Color(0xFF10B981),
                            ),
                            const SizedBox(height: AppSpacing.sm),
                            Text(
                              'Semua Permohonan Telah Ditinjau!',
                              style: AppTypography.heading3.copyWith(
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              'Tidak ada permohonan surat yang membutuhkan tanda tangan Anda saat ini.',
                              style: AppTypography.caption.copyWith(
                                color: AppColors.textSecondary,
                              ),
                              textAlign: TextAlign.center,
                            ),
                          ],
                        ),
                      );
                    }

                    // Display top 3 priority requests
                    return Column(
                      children: pending.take(3).map((item) {
                        final id = item['pengajuan_id'] as int? ?? 0;
                        final namaWarga =
                            item['nama_warga']?.toString() ?? 'Warga RT 04';
                        final nik = item['nik']?.toString() ?? '-';
                        final namaSurat =
                            item['nama_surat']?.toString() ?? 'Surat Pengantar';
                        final nomorPengajuan =
                            item['nomor_pengajuan']?.toString() ?? '-';
                        final keperluan =
                            item['keperluan']?.toString() ?? '-';
                        final status =
                            item['status']?.toString() ?? 'diajukan';

                        return Padding(
                          padding: const EdgeInsets.only(bottom: AppSpacing.md),
                          child: _buildQueueCard(
                            context,
                            id: id,
                            namaWarga: namaWarga,
                            nik: nik,
                            namaSurat: namaSurat,
                            nomorPengajuan: nomorPengajuan,
                            keperluan: keperluan,
                            status: status,
                          ),
                        );
                      }).toList(),
                    );
                  },
                ),
                const SizedBox(height: AppSpacing.lg),

                // Quick Navigation Cards
                Text(
                  'Fitur Administrasi',
                  style: AppTypography.heading3.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: AppSpacing.sm),
                _buildQuickActionTile(
                  context,
                  title: 'Buka Antrean Verifikasi Lengkap',
                  subtitle:
                      'Tinjau draf surat, verifikasi data, dan proses pengesahan tanda tangan.',
                  icon: Icons.checklist_rtl_rounded,
                  iconColor: AppColors.primaryAccent,
                  onTap: () => context.push(RouteNames.rtQueue),
                ),
                const SizedBox(height: AppSpacing.sm),
                _buildQuickActionTile(
                  context,
                  title: 'TanyaRT — Basis Informasi Lingkungan',
                  subtitle:
                      'Periksa kebijakan RT, SOP layanan, dan data warga terpadu.',
                  icon: Icons.smart_toy_rounded,
                  iconColor: const Color(0xFF6366F1),
                  onTap: () => context.push(RouteNames.chatbot),
                ),
                const SizedBox(height: 40),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildMetricCard({
    required String title,
    required String count,
    required IconData icon,
    required Color textColor,
    required Color bgColor,
    required Color borderColor,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: borderColor),
        boxShadow: const [
          BoxShadow(
            color: Color(0x04000000),
            blurRadius: 6,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Icon(icon, color: textColor, size: 20),
              Text(
                count,
                style: AppTypography.heading1.copyWith(
                  fontWeight: FontWeight.w800,
                  fontSize: 22,
                  color: textColor,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            title,
            style: AppTypography.caption.copyWith(
              fontWeight: FontWeight.w700,
              color: textColor,
              fontSize: 11,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }

  Widget _buildQueueCard(
    BuildContext context, {
    required int id,
    required String namaWarga,
    required String nik,
    required String namaSurat,
    required String nomorPengajuan,
    required String keperluan,
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
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                // Initials Avatar
                CircleAvatar(
                  radius: 20,
                  backgroundColor: const Color(0xFFEFF6FF),
                  child: Text(
                    initials,
                    style: AppTypography.labelBold.copyWith(
                      color: AppColors.primaryAccent,
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
                        style: AppTypography.labelBold.copyWith(fontSize: 14),
                      ),
                      Text(
                        'NIK: $nik',
                        style: AppTypography.caption.copyWith(
                          color: AppColors.textSecondary,
                          fontSize: 11,
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
            Row(
              children: [
                Text(
                  nomorPengajuan,
                  style: AppTypography.caption.copyWith(
                    fontWeight: FontWeight.w600,
                    color: AppColors.textMuted,
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
                  icon: const Icon(Icons.draw_rounded, size: 16),
                  label: Text(
                    'Review & TTD',
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
    );
  }

  Widget _buildQuickActionTile(
    BuildContext context, {
    required String title,
    required String subtitle,
    required IconData icon,
    required Color iconColor,
    required VoidCallback onTap,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: ListTile(
        onTap: onTap,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.md,
          vertical: 4,
        ),
        leading: Container(
          width: 42,
          height: 42,
          decoration: BoxDecoration(
            color: iconColor.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(icon, color: iconColor, size: 22),
        ),
        title: Text(
          title,
          style: AppTypography.labelBold.copyWith(fontSize: 14),
        ),
        subtitle: Text(
          subtitle,
          style: AppTypography.caption.copyWith(
            color: AppColors.textSecondary,
            fontSize: 12,
          ),
        ),
        trailing: const Icon(
          Icons.arrow_forward_ios_rounded,
          size: 16,
          color: AppColors.textSecondary,
        ),
      ),
    );
  }
}
