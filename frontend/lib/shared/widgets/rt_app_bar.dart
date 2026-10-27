import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_typography.dart';

/// COMP-SHR-002: RTAppBar
class RTAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String? title;
  final bool showLogo;
  final VoidCallback? onMenuPressed;
  final List<Widget>? actions;

  const RTAppBar({
    super.key,
    this.title,
    this.showLogo = true,
    this.onMenuPressed,
    this.actions,
  });

  @override
  Widget build(BuildContext context) {
    return AppBar(
      leading: IconButton(
        icon: const Icon(Icons.menu, color: AppColors.secondaryDark),
        onPressed: onMenuPressed ?? () => Scaffold.of(context).openDrawer(),
      ),
      title: showLogo
          ? Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: AppSpacing.spaceXS,
                    vertical: AppSpacing.space2XS,
                  ),
                  decoration: BoxDecoration(
                    color: AppColors.secondaryDark,
                    borderRadius: BorderRadius.circular(AppSpacing.radiusXS),
                  ),
                  child: const Text(
                    'logo',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                ),
                const SizedBox(width: AppSpacing.spaceXS),
                Text(
                  title ?? 'RTConnect',
                  style: AppTypography.titleMedium.copyWith(
                    fontWeight: FontWeight.w700,
                    letterSpacing: -0.3,
                  ),
                ),
              ],
            )
          : Text(title ?? '', style: AppTypography.titleLarge),
      actions: actions,
      bottom: const PreferredSize(
        preferredSize: Size.fromHeight(1.0),
        child: Divider(height: 1.0, color: AppColors.border),
      ),
    );
  }

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight + 1.0);
}
