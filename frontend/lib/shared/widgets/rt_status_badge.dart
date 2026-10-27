import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_typography.dart';

/// COMP-CORE-004: RTStatusBadge grounded in Figma Hi-Fi Badges (Pill 9999px, exact text colors)
class RTStatusBadge extends StatelessWidget {
  final String status;
  final bool showDot;

  const RTStatusBadge({
    super.key,
    required this.status,
    this.showDot = false,
  });

  @override
  Widget build(BuildContext context) {
    Color bg;
    Color fg;
    String label;

    switch (status.toLowerCase()) {
      case 'diajukan':
      case 'menunggu_review':
      case 'menunggu review':
        bg = AppColors.statusDiajukanBg;
        fg = AppColors.statusDiajukan;
        label = 'Diajukan';
        break;
      case 'diproses':
        bg = const Color(0xFFDBEAFE);
        fg = AppColors.primaryAccent;
        label = 'Diproses';
        break;
      case 'perlu_revisi':
      case 'perlu revisi':
      case 'revisi':
        bg = AppColors.statusRevisiBg;
        fg = AppColors.statusRevisi;
        label = 'Perlu Revisi';
        break;
      case 'menunggu':
        bg = AppColors.statusMenungguBg;
        fg = AppColors.statusMenunggu;
        label = 'Menunggu';
        break;
      case 'disetujui':
        bg = AppColors.statusDisetujuiBg;
        fg = AppColors.statusDisetujui;
        label = 'Disetujui';
        break;
      case 'siap_diambil':
      case 'siap diambil':
        bg = AppColors.statusSiapDiambilBg;
        fg = AppColors.statusSiapDiambil;
        label = 'Siap Diambil';
        break;
      case 'selesai':
        bg = AppColors.statusSelesaiBg;
        fg = AppColors.statusSelesai;
        label = 'Selesai';
        break;
      case 'ditolak':
        bg = AppColors.statusDitolakBg;
        fg = AppColors.statusDitolak;
        label = 'Ditolak';
        break;
      default:
        bg = AppColors.surfaceAlt;
        fg = AppColors.textSecondary;
        label = status;
        break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10.0, vertical: 4.0),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(9999.0),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (showDot) ...[
            Container(
              width: 6,
              height: 6,
              decoration: BoxDecoration(
                color: fg,
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: 5),
          ],
          Text(
            label,
            style: AppTypography.labelSmall.copyWith(
              color: fg,
              fontWeight: FontWeight.w700,
              fontSize: 11.0,
            ),
          ),
        ],
      ),
    );
  }
}
