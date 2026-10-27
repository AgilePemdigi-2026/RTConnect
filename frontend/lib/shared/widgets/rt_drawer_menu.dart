import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/router/route_names.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_typography.dart';
import '../../features/auth/presentation/auth_controller.dart';
import '../../features/notifications/presentation/notification_controller.dart';

/// COMP-SHR-003: RTDrawerMenu grounded in Figma Hi-Fi "Profile Side Drawer - RTConnect" (#68:1902)
class RTDrawerMenu extends ConsumerWidget {
  final String? userName;
  final String? userEmail;
  final String? userRole;
  final String? neighborhood;
  final VoidCallback? onLogout;

  const RTDrawerMenu({
    super.key,
    this.userName,
    this.userEmail,
    this.userRole,
    this.neighborhood = 'RT 04 / RW 07, Tawangsari',
    this.onLogout,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authControllerProvider);
    final user = authState.user;

    final effectiveName = userName ?? user?.namaLengkap ?? 'Warga RT 04';
    final effectiveEmail = userEmail ?? user?.email ?? 'warga@rtconnect.id';
    final effectiveRole = userRole ?? (user?.role ?? 'warga');
    final isRT = effectiveRole.toLowerCase() == 'rt';
    final unreadNotificationCount = ref.watch(unreadNotificationCountProvider);

    return Drawer(
      width: 335.0,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.only(
          topLeft: Radius.circular(32.0),
          bottomLeft: Radius.circular(32.0),
        ),
      ),
      child: SafeArea(
        child: Column(
          children: [
            // Top Bar: Close Button & Role Badge
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 12.0),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  InkWell(
                    onTap: () => Navigator.pop(context),
                    borderRadius: BorderRadius.circular(9999.0),
                    child: Container(
                      padding: const EdgeInsets.all(8.0),
                      decoration: const BoxDecoration(
                        color: AppColors.surfaceNeutral,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.close_rounded, size: 20, color: AppColors.textPrimary),
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10.0, vertical: 4.0),
                    decoration: BoxDecoration(
                      color: isRT ? const Color(0xFFDBEAFE) : AppColors.surfaceNeutral,
                      borderRadius: BorderRadius.circular(9999.0),
                    ),
                    child: Text(
                      isRT ? 'Ketua RT' : 'Warga',
                      style: AppTypography.labelSmall.copyWith(
                        color: isRT ? AppColors.primaryAccent : AppColors.textSecondary,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            const Divider(color: AppColors.border, height: 1),

            // Profile Header Section
            Expanded(
              child: ListView(
                padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 16.0),
                children: [
                  Center(
                    child: Stack(
                      children: [
                        Container(
                          width: 80,
                          height: 80,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            gradient: const LinearGradient(
                              colors: [Color(0xFF2563EB), Color(0xFF1D4ED8)],
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                            ),
                            boxShadow: [
                              BoxShadow(
                                color: const Color(0xFF1E3A8A).withValues(alpha: 0.25),
                                blurRadius: 15,
                                offset: const Offset(0, 8),
                              ),
                            ],
                          ),
                          child: Center(
                            child: Text(
                              effectiveName.isNotEmpty ? effectiveName[0].toUpperCase() : 'U',
                              style: const TextStyle(
                                fontSize: 32,
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ),
                        Positioned(
                          right: 2,
                          bottom: 2,
                          child: Container(
                            width: 18,
                            height: 18,
                            decoration: BoxDecoration(
                              color: AppColors.success,
                              shape: BoxShape.circle,
                              border: Border.all(color: Colors.white, width: 2.5),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        'Halo, ',
                        style: AppTypography.titleMedium.copyWith(color: AppColors.textPrimary),
                      ),
                      Flexible(
                        child: Text(
                          effectiveName,
                          overflow: TextOverflow.ellipsis,
                          style: AppTypography.titleMedium.copyWith(color: AppColors.textPrimary),
                        ),
                      ),
                      const SizedBox(width: 4),
                      const Icon(Icons.verified_rounded, size: 18, color: AppColors.primaryAction),
                    ],
                  ),
                  const SizedBox(height: 2),
                  Text(
                    effectiveEmail,
                    textAlign: TextAlign.center,
                    style: AppTypography.bodySmall.copyWith(color: AppColors.textMuted),
                  ),
                  const SizedBox(height: 6),
                  Center(
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10.0, vertical: 3.0),
                      decoration: BoxDecoration(
                        color: AppColors.surfaceAlt,
                        borderRadius: BorderRadius.circular(9999.0),
                      ),
                      child: Text(
                        neighborhood ?? 'RT 04 / RW 07, Tawangsari',
                        style: AppTypography.labelSmall.copyWith(
                          fontSize: 11.0,
                          color: AppColors.textMuted,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Menu Items
                  _buildDrawerMenuTile(
                    icon: Icons.person_outline_rounded,
                    title: 'Profil Saya',
                    onTap: () => Navigator.pop(context),
                  ),
                  _buildDrawerMenuTile(
                    icon: Icons.assignment_outlined,
                    title: isRT ? 'Daftar Pengajuan' : 'Riwayat Pengajuan',
                    onTap: () {
                      Navigator.pop(context);
                      context.push(isRT ? RouteNames.rtQueue : RouteNames.wargaPengajuan);
                    },
                  ),
                  _buildDrawerMenuTile(
                    icon: Icons.notifications_none_rounded,
                    title: 'Notifikasi',
                    badge: unreadNotificationCount > 0
                        ? Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: AppColors.badgeNotification,
                              borderRadius: BorderRadius.circular(9999),
                            ),
                            child: Text(
                              unreadNotificationCount > 99
                                  ? '99+ Baru'
                                  : '$unreadNotificationCount Baru',
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          )
                        : null,
                    onTap: () async {
                      Navigator.pop(context);
                      await context.push(RouteNames.notifications);
                      ref.invalidate(notificationsProvider);
                    },
                  ),
                  _buildDrawerMenuTile(
                    icon: Icons.settings_outlined,
                    title: 'Pengaturan Akun',
                    onTap: () => Navigator.pop(context),
                  ),
                  _buildDrawerMenuTile(
                    icon: Icons.help_outline_rounded,
                    title: 'Pusat Bantuan & TanyaRT',
                    onTap: () {
                      Navigator.pop(context);
                      context.push(RouteNames.chatbot);
                    },
                  ),
                ],
              ),
            ),

            // Footer Logout
            Padding(
              padding: const EdgeInsets.all(20.0),
              child: Container(
                width: double.infinity,
                height: 48,
                decoration: BoxDecoration(
                  color: AppColors.errorDark,
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.errorDark.withValues(alpha: 0.25),
                      blurRadius: 8,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: Material(
                  color: Colors.transparent,
                  child: InkWell(
                    borderRadius: BorderRadius.circular(16),
                    onTap: () async {
                      Navigator.pop(context);
                      if (onLogout != null) {
                        onLogout!();
                      } else {
                        await ref.read(authControllerProvider.notifier).logout();
                        if (context.mounted) context.go(RouteNames.login);
                      }
                    },
                    child: const Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.power_settings_new_rounded, color: Colors.white, size: 20),
                        SizedBox(width: 8),
                        Text(
                          'Log Out',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 0.5,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDrawerMenuTile({
    required IconData icon,
    required String title,
    Widget? badge,
    required VoidCallback onTap,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8.0),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(12.0),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 10.0, vertical: 10.0),
            child: Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: AppColors.surfaceAlt,
                    borderRadius: BorderRadius.circular(10.0),
                  ),
                  child: Icon(icon, color: AppColors.textSlate, size: 20),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Text(
                    title,
                    style: AppTypography.bodyLarge.copyWith(
                      fontWeight: FontWeight.w600,
                      color: AppColors.textSlate,
                    ),
                  ),
                ),
                if (badge != null) ...[
                  badge,
                  const SizedBox(width: 8),
                ],
                const Icon(Icons.chevron_right_rounded, size: 18, color: AppColors.textSubtle),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
