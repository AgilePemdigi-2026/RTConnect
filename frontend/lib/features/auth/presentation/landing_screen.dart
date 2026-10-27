import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/router/route_names.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_typography.dart';
import '../../../shared/widgets/rt_primary_button.dart';
import '../../../shared/widgets/rt_secondary_button.dart';

/// SCREEN-001: Landing Page - RTConnect (Figma Node #68:1751)
class LandingScreen extends StatelessWidget {
  const LandingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              const SizedBox(height: 12),

              // Hero Civic Illustration Card (Clean Vector Civic Building & RESMI RT badge)
              Container(
                width: double.infinity,
                height: 230,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [
                      Color(0xB3EFF6FF), // rgba(239, 246, 255, 0.7)
                      Color(0x80EEF2FF), // rgba(238, 242, 255, 0.5)
                    ],
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                  ),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: const Color(0xB3DBEAFE), // rgba(219, 234, 254, 0.7)
                    width: 1,
                  ),
                  boxShadow: const [
                    BoxShadow(
                      color: Color(0x0D000000),
                      blurRadius: 4,
                      offset: Offset(0, 1),
                    ),
                  ],
                ),
                child: Stack(
                  clipBehavior: Clip.none,
                  children: [
                    // Geometric decorative accents
                    Positioned(
                      top: -10,
                      right: -10,
                      child: Container(
                        width: 90,
                        height: 90,
                        decoration: const BoxDecoration(
                          shape: BoxShape.circle,
                          color: Color(0x4DBFDBFE),
                        ),
                      ),
                    ),
                    Positioned(
                      bottom: -15,
                      left: -15,
                      child: Container(
                        width: 80,
                        height: 80,
                        decoration: const BoxDecoration(
                          shape: BoxShape.circle,
                          color: Color(0x33A7F3D0),
                        ),
                      ),
                    ),

                    // Central Civic Graphics
                    Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          // Civic Building & Shield Composition
                          Stack(
                            alignment: Alignment.center,
                            children: [
                              Container(
                                width: 96,
                                height: 96,
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  shape: BoxShape.circle,
                                  border: Border.all(
                                    color: const Color(0xFFDBEAFE),
                                    width: 2,
                                  ),
                                  boxShadow: [
                                    BoxShadow(
                                      color: const Color(0xFF1D4ED8).withValues(alpha: 0.12),
                                      blurRadius: 16,
                                      offset: const Offset(0, 4),
                                    ),
                                  ],
                                ),
                                child: const Center(
                                  child: Icon(
                                    Icons.account_balance_rounded,
                                    size: 46,
                                    color: AppColors.primaryBrand,
                                  ),
                                ),
                              ),

                              // Indonesian Flag element on top-left of building
                              Positioned(
                                top: 0,
                                left: 6,
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: Colors.white,
                                    borderRadius: BorderRadius.circular(4),
                                    border: Border.all(color: AppColors.border, width: 0.5),
                                    boxShadow: const [
                                      BoxShadow(color: Color(0x14000000), blurRadius: 2),
                                    ],
                                  ),
                                  child: Column(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Container(width: 14, height: 4, color: AppColors.error),
                                      Container(width: 14, height: 4, color: Colors.white),
                                    ],
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),

                          // RESMI RT Badge
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: AppColors.successDark,
                              borderRadius: BorderRadius.circular(9999),
                              boxShadow: const [
                                BoxShadow(
                                  color: Color(0x33059669),
                                  blurRadius: 6,
                                  offset: Offset(0, 2),
                                ),
                              ],
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const Icon(Icons.verified_user_rounded, size: 13, color: Colors.white),
                                const SizedBox(width: 4),
                                Text(
                                  'RESMI RT',
                                  style: AppTypography.badgeUppercase.copyWith(
                                    fontSize: 10,
                                    color: Colors.white,
                                    fontWeight: FontWeight.w800,
                                    letterSpacing: 0.5,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 28),

              // SELAMAT DATANG DI Badge
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
                decoration: BoxDecoration(
                  color: AppColors.primaryBg,
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  'SELAMAT DATANG DI',
                  style: AppTypography.badgeUppercase.copyWith(
                    color: AppColors.primaryBrand,
                    fontSize: 11,
                    letterSpacing: 0.6,
                  ),
                ),
              ),

              const SizedBox(height: 8),

              // Title RTConnect
              Text(
                'RTConnect',
                style: AppTypography.heroTitle.copyWith(
                  color: AppColors.textPrimary,
                  fontSize: 32,
                  fontWeight: FontWeight.w800,
                ),
              ),

              const SizedBox(height: 8),

              // Subtitles matching Figma Verbatim
              Text(
                'Administrasi warga lebih mudah, cepat, dan transparan.',
                textAlign: TextAlign.center,
                style: AppTypography.bodyLarge.copyWith(
                  color: AppColors.textSlate,
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                  height: 1.4,
                ),
              ),

              const SizedBox(height: 6),

              Text(
                'Ajukan surat dan dapatkan informasi layanan RT dalam satu platform.',
                textAlign: TextAlign.center,
                style: AppTypography.bodySmall.copyWith(
                  color: AppColors.textMuted,
                  fontSize: 12,
                  height: 1.5,
                ),
              ),

              const SizedBox(height: 36),

              // Action Buttons matching Figma
              RTPrimaryButton(
                text: 'Masuk ke aplikasi RTConnect',
                trailingIcon: Icons.arrow_forward_rounded,
                height: 52,
                borderRadius: 12,
                onPressed: () => context.push(RouteNames.login),
              ),

              const SizedBox(height: 12),

              RTSecondaryButton(
                text: 'Registrasi',
                height: 50,
                borderRadius: 12,
                onPressed: () => context.push(RouteNames.register),
              ),

              const SizedBox(height: 28),

              // Footer Note / Demo server badge
              Text(
                '${AppConstants.rtArea} • ${AppConstants.appName}',
                style: AppTypography.caption.copyWith(color: AppColors.textSubtle),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
