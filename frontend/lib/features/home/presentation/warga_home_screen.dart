import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/router/route_names.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_typography.dart';
import '../../../shared/widgets/rt_bottom_nav_bar.dart';
import '../../../shared/widgets/rt_drawer_menu.dart';
import '../../../shared/widgets/rt_status_badge.dart';
import '../../auth/presentation/auth_controller.dart';
import '../../letters/presentation/letter_controller.dart';
import '../../notifications/presentation/notification_controller.dart';

/// Screen 4: Beranda Warga (Figma Node #68:3029)
class WargaHomeScreen extends ConsumerWidget {
  const WargaHomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authControllerProvider);
    final user = authState.user;
    final myAppsAsync = ref.watch(myApplicationsProvider);
    final unreadNotifs = ref.watch(unreadNotificationCountProvider);

    final namaWarga = user?.namaLengkap ?? 'Warga RT 04';
    final initial = namaWarga.isNotEmpty ? namaWarga[0].toUpperCase() : 'W';

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
                          color: AppColors.secondary,
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          'WARGA',
                          style: AppTypography.caption.copyWith(
                            color: AppColors.primary,
                            fontWeight: FontWeight.w700,
                            fontSize: 10,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const Spacer(),

                  // Notification Bell with unread dot
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

                  // Avatar profile triggering RTDrawerMenu
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
                            color: AppColors.primary,
                            border: Border.all(
                              color: AppColors.primaryAccent,
                              width: 2,
                            ),
                            boxShadow: const [
                              BoxShadow(
                                color: Color(0x1A000000),
                                blurRadius: 4,
                                offset: Offset(0, 2),
                              ),
                            ],
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
            ref.invalidate(myApplicationsProvider);
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
                        '${AppConstants.rtArea} • Griya Taman Asri',
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

                // Greeting Header
                Text(
                  'Selamat datang, $namaWarga 👋',
                  style: AppTypography.heading1.copyWith(
                    fontWeight: FontWeight.w800,
                    color: AppColors.textPrimary,
                    fontSize: 22,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Ajukan surat pengantar dan pantau status permohonan dengan mudah.',
                  style: AppTypography.bodySmall.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
                const SizedBox(height: AppSpacing.lg),

                // 2 Layanan Utama Header
                Text(
                  'Layanan Utama',
                  style: AppTypography.heading3.copyWith(
                    color: AppColors.textPrimary,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: AppSpacing.md),

                // 2 Layanan Utama Cards
                Row(
                  children: [
                    // Card 1: Ajukan Surat
                    Expanded(
                      child: _buildMainServiceCard(
                        context,
                        title: 'Ajukan Surat',
                        subtitle: 'Buat surat pengantar RT baru secara digital',
                        icon: Icons.edit_document,
                        iconBgColor: AppColors.primaryAccent,
                        cardBgColor: Colors.white,
                        onTap: () =>
                            context.push(RouteNames.wargaPengajuanBaru),
                      ),
                    ),
                    const SizedBox(width: AppSpacing.md),
                    // Card 2: TanyaRT
                    Expanded(
                      child: _buildMainServiceCard(
                        context,
                        title: 'TanyaRT',
                        subtitle: 'Asisten AI pintar untuk info & SOP lingkungan',
                        icon: Icons.smart_toy_rounded,
                        iconBgColor: const Color(0xFF6366F1),
                        cardBgColor: Colors.white,
                        onTap: () => context.push(RouteNames.chatbot),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: AppSpacing.xl),

                // Section Pengajuan Terbaru
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Pengajuan Terbaru',
                      style: AppTypography.heading3.copyWith(
                        color: AppColors.textPrimary,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    TextButton(
                      onPressed: () => context.push(RouteNames.wargaPengajuan),
                      style: TextButton.styleFrom(
                        padding: EdgeInsets.zero,
                        minimumSize: Size.zero,
                        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      ),
                      child: Text(
                        'Lihat Semua',
                        style: AppTypography.labelBold.copyWith(
                          color: AppColors.primaryAccent,
                          fontSize: 13,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: AppSpacing.md),

                // Latest Application Status Card
                myAppsAsync.when(
                  loading: () => Container(
                    height: 140,
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppColors.border),
                    ),
                    child: const Center(child: CircularProgressIndicator()),
                  ),
                  error: (err, _) => Container(
                    padding: const EdgeInsets.all(AppSpacing.md),
                    decoration: BoxDecoration(
                      color: const Color(0xFFFEF2F2),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: const Color(0xFFFECACA)),
                    ),
                    child: Text(
                      'Gagal memuat status pengajuan: $err',
                      style: AppTypography.caption.copyWith(
                        color: AppColors.error,
                      ),
                    ),
                  ),
                  data: (apps) {
                    if (apps.isEmpty) {
                      return _buildEmptyApplicationCard(context);
                    }
                    final latest = apps.first;
                    return _buildActiveApplicationCard(context, latest);
                  },
                ),
                const SizedBox(height: AppSpacing.xl),

                // Community Quick Info Banner (Figma civic info)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(AppSpacing.md),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF0FDF4),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: const Color(0xFFBBF7D0)),
                  ),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: const Color(0xFFDCFCE7),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Icon(
                          Icons.campaign_rounded,
                          color: Color(0xFF16A34A),
                          size: 24,
                        ),
                      ),
                      const SizedBox(width: AppSpacing.md),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Informasi Warga',
                              style: AppTypography.labelBold.copyWith(
                                color: const Color(0xFF166534),
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              'Iuran keamanan & kebersihan bulan ini telah aktif. Terima kasih atas partisipasi aktif warga.',
                              style: AppTypography.caption.copyWith(
                                color: const Color(0xFF15803D),
                                height: 1.3,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 40),
              ],
            ),
          ),
        ),
      ),
      bottomNavigationBar: RTBottomNavBar(
        currentIndex: 0,
        onTap: (index) {
          if (index == 0) return;
          if (index == 1) {
            context.push(RouteNames.wargaPengajuan);
          } else if (index == 2) {
            context.push(RouteNames.chatbot);
          }
        },
      ),
    );
  }

  Widget _buildMainServiceCard(
    BuildContext context, {
    required String title,
    required String subtitle,
    required IconData icon,
    required Color iconBgColor,
    required Color cardBgColor,
    required VoidCallback onTap,
  }) {
    return Material(
      color: cardBgColor,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.all(AppSpacing.md),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.border),
            boxShadow: const [
              BoxShadow(
                color: Color(0x06000000),
                blurRadius: 10,
                offset: Offset(0, 4),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Container(
                    width: 44,
                    height: 44,
                    decoration: BoxDecoration(
                      color: iconBgColor.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Icon(icon, color: iconBgColor, size: 24),
                  ),
                  Container(
                    width: 28,
                    height: 28,
                    decoration: BoxDecoration(
                      color: AppColors.surface,
                      shape: BoxShape.circle,
                      border: Border.all(color: AppColors.border),
                    ),
                    child: const Icon(
                      Icons.arrow_forward_rounded,
                      size: 16,
                      color: AppColors.textSecondary,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.md),
              Text(
                title,
                style: AppTypography.heading3.copyWith(
                  fontWeight: FontWeight.w700,
                  fontSize: 16,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                subtitle,
                style: AppTypography.caption.copyWith(
                  color: AppColors.textSecondary,
                  height: 1.3,
                  fontSize: 12,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildActiveApplicationCard(
    BuildContext context,
    Map<String, dynamic> app,
  ) {
    final id = app['pengajuan_id'] as int? ?? 0;
    final namaSurat = app['nama_surat']?.toString() ?? 'Surat Pengantar RT';
    final nomorPengajuan = app['nomor_pengajuan']?.toString() ?? '-';
    final status = app['status']?.toString().toLowerCase() ?? 'diajukan';

    // Timeline calculation based on status
    const isSubmitted = true;
    final isProcessing =
        status == 'diproses' || status == 'perlu revisi' || status == 'disetujui' || status == 'selesai';
    final isDone = status == 'selesai';
    final isRevision = status == 'perlu revisi';

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
        boxShadow: const [
          BoxShadow(
            color: Color(0x06000000),
            blurRadius: 10,
            offset: Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header Card
          Padding(
            padding: const EdgeInsets.all(AppSpacing.md),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    color: AppColors.secondary,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(
                    Icons.mark_email_read_outlined,
                    color: AppColors.primary,
                    size: 24,
                  ),
                ),
                const SizedBox(width: AppSpacing.md),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        namaSurat,
                        style: AppTypography.heading3.copyWith(
                          fontWeight: FontWeight.w700,
                          fontSize: 15,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'Nomor: $nomorPengajuan',
                        style: AppTypography.caption.copyWith(
                          color: AppColors.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ),
                RTStatusBadge(status: status),
              ],
            ),
          ),

          const Divider(height: 1, color: AppColors.border),

          // 3-Step Horizontal Timeline matching Figma #68:3029
          Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.md,
              vertical: AppSpacing.md,
            ),
            child: Row(
              children: [
                _buildTimelineNode(
                  label: 'Diajukan',
                  isActive: isSubmitted,
                  isCompleted: isProcessing,
                  icon: Icons.check,
                ),
                Expanded(
                  child: Container(
                    height: 2,
                    color: isProcessing ? AppColors.primaryAccent : AppColors.border,
                  ),
                ),
                _buildTimelineNode(
                  label: isRevision ? 'Perlu Revisi' : 'Verifikasi RT',
                  isActive: isProcessing,
                  isCompleted: isDone,
                  icon: isRevision ? Icons.warning_amber_rounded : Icons.person_search,
                  highlightColor: isRevision ? AppColors.warning : AppColors.primaryAccent,
                ),
                Expanded(
                  child: Container(
                    height: 2,
                    color: isDone ? AppColors.primaryAccent : AppColors.border,
                  ),
                ),
                _buildTimelineNode(
                  label: 'Selesai',
                  isActive: isDone,
                  isCompleted: isDone,
                  icon: Icons.verified,
                ),
              ],
            ),
          ),

          // Detail CTA Bar
          InkWell(
            onTap: () => context.push('/letters/$id'),
            borderRadius: const BorderRadius.vertical(bottom: Radius.circular(16)),
            child: Container(
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.md,
                vertical: 12,
              ),
              decoration: const BoxDecoration(
                color: Color(0xFFF8FAFC),
                borderRadius: BorderRadius.vertical(bottom: Radius.circular(16)),
                border: Border(top: BorderSide(color: AppColors.border)),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Lihat Detail & Status Surat',
                    style: AppTypography.labelBold.copyWith(
                      color: AppColors.primaryAccent,
                      fontSize: 13,
                    ),
                  ),
                  const Icon(
                    Icons.chevron_right_rounded,
                    color: AppColors.primaryAccent,
                    size: 20,
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTimelineNode({
    required String label,
    required bool isActive,
    required bool isCompleted,
    required IconData icon,
    Color? highlightColor,
  }) {
    final activeColor = highlightColor ?? AppColors.primaryAccent;
    final color = isCompleted
        ? const Color(0xFF10B981)
        : (isActive ? activeColor : AppColors.textMuted);

    return Column(
      children: [
        Container(
          width: 28,
          height: 28,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: isCompleted
                ? const Color(0xFF10B981)
                : (isActive ? activeColor.withValues(alpha: 0.15) : AppColors.surface),
            border: Border.all(
              color: color,
              width: 2,
            ),
          ),
          child: Icon(
            icon,
            size: 14,
            color: isCompleted ? Colors.white : color,
          ),
        ),
        const SizedBox(height: 6),
        Text(
          label,
          style: AppTypography.caption.copyWith(
            fontWeight: isActive ? FontWeight.w700 : FontWeight.w500,
            color: isActive ? AppColors.textPrimary : AppColors.textMuted,
            fontSize: 11,
          ),
        ),
      ],
    );
  }

  Widget _buildEmptyApplicationCard(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(AppSpacing.lg),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        children: [
          Container(
            width: 56,
            height: 56,
            decoration: const BoxDecoration(
              color: AppColors.secondary,
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.note_alt_outlined,
              color: AppColors.primaryAccent,
              size: 28,
            ),
          ),
          const SizedBox(height: AppSpacing.md),
          Text(
            'Belum ada pengajuan surat',
            style: AppTypography.heading3.copyWith(
              fontWeight: FontWeight.w700,
              fontSize: 15,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'Anda belum memiliki pengajuan surat aktif saat ini.',
            style: AppTypography.caption.copyWith(
              color: AppColors.textSecondary,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: AppSpacing.md),
          ElevatedButton(
            onPressed: () => context.push(RouteNames.wargaPengajuanBaru),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primaryAccent,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
              ),
              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
            ),
            child: Text(
              'Ajukan Surat Sekarang',
              style: AppTypography.labelBold.copyWith(color: Colors.white),
            ),
          ),
        ],
      ),
    );
  }
}
