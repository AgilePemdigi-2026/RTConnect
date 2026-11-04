import 'dart:ui';
import 'package:flutter/material.dart';
import '../../core/theme/app_typography.dart';

/// COMP-SHR-001: RTBottomNavBar grounded in Figma Hi-Fi Navigation
/// Stateless persistent navigation bar at the bottom of the screen.
class RTBottomNavBar extends StatelessWidget {
  final int currentIndex;
  final ValueChanged<int> onTap;

  const RTBottomNavBar({
    super.key,
    required this.currentIndex,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 12.0, sigmaY: 12.0),
        child: Container(
          height: 64.0,
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.95),
            border: const Border(
              top: BorderSide(color: Color(0xFFECEEF0), width: 1.0),
            ),
            boxShadow: const [
              BoxShadow(
                color: Color(0x0A000000),
                blurRadius: 8,
                offset: Offset(0, -1),
              ),
            ],
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _buildNavItem(
                index: 0,
                icon: Icons.assignment_outlined,
                label: 'Pengajuan',
              ),
              _buildNavItem(
                index: 1,
                icon: Icons.home_rounded,
                label: 'Beranda',
              ),
              _buildNavItem(
                index: 2,
                icon: Icons.forum_outlined,
                label: 'TanyaRT',
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem({
    required int index,
    required IconData icon,
    required String label,
  }) {
    final isSelected = currentIndex == index;
    const activeColor = Color(0xFF0051D5);
    const inactiveColor = Color(0xFF43474D);

    return InkWell(
      onTap: () => onTap(index),
      borderRadius: BorderRadius.circular(16.0),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 4.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14.0, vertical: 4.0),
              decoration: BoxDecoration(
                color: isSelected
                    ? const Color(0xFFDBE1FF).withValues(alpha: 0.5)
                    : Colors.transparent,
                borderRadius: BorderRadius.circular(9999.0),
              ),
              child: Icon(
                icon,
                color: isSelected ? activeColor : inactiveColor,
                size: 22,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: AppTypography.labelSmall.copyWith(
                color: isSelected ? activeColor : inactiveColor,
                fontWeight: isSelected ? FontWeight.w700 : FontWeight.w600,
                fontSize: 11.0,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
