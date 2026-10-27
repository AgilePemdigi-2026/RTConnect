import 'package:flutter/material.dart';

/// Design Tokens: Colors for RTConnect grounded in Figma Hi-Fi Design (Node 137:604)
class AppColors {
  // Brand & Primary Blues
  static const Color primaryBrand = Color(0xFF1D4ED8); // Figma #1D4ED8 (Blue 700)
  static const Color primary = primaryBrand;
  static const Color primaryAction = Color(0xFF2563EB); // Figma #2563EB (Blue 600)
  static const Color primaryDark = Color(0xFF1E40AF); // Figma #1E40AF (Blue 800)
  static const Color primaryLight = Color(0xFF3B82F6); // Figma #3B82F6 (Blue 500)
  static const Color primaryAccent = Color(0xFF0051D5); // Figma #0051D5 (Vibrant Royal)
  static const Color primaryContainer = Color(0xFFDBEAFE); // Figma #DBEAFE (Blue 100)
  static const Color secondary = primaryContainer; // Convenient alias for light blue container
  static const Color primaryBg = Color(0xFFEFF6FF); // Figma #EFF6FF (Blue 50)
  static const Color lightContainer = Color(0xFFEDF0FF); // Figma #EDF0FF (Container tinted)

  // Deep Navy Tones
  static const Color navyDark = Color(0xFF00152A); // Figma #00152A
  static const Color navyDeep = Color(0xFF0B1C30); // Figma #0B1C30
  static const Color navyHeader = Color(0xFF102A43); // Figma #102A43
  static const Color secondaryDark = Color(0xFF0F172A); // Slate 900

  // Brand Accents & Utilities
  static const Color brandWhatsApp = Color(0xFF059669); // WhatsApp Emerald
  static const Color success = Color(0xFF10B981); // Emerald 500
  static const Color successDark = Color(0xFF059669); // Emerald 600
  static const Color error = Color(0xFFDC2626); // Red 600
  static const Color errorDark = Color(0xFFBA1A1A); // Red 700 (Figma Logout & Alerts)
  static const Color warning = Color(0xFFD97706); // Amber 600
  static const Color badgeNotification = Color(0xFFF43F5E); // Rose 500 (Figma Unread)

  // Surfaces & Backgrounds
  static const Color background = Color(0xFFF8FAFC); // Slate 50
  static const Color canvasBg = Color(0xFFF7F9FB); // Figma #F7F9FB
  static const Color surface = Color(0xFFFFFFFF);
  static const Color cardBackground = surface;
  static const Color surfaceAlt = Color(0xFFF2F4F6); // Figma #F2F4F6
  static const Color surfaceNeutral = Color(0xFFECEEF0); // Figma #ECEEF0
  static const Color border = Color(0xFFE2E8F0); // Figma #E2E8F0 (Slate 200)
  static const Color borderSubtle = Color(0xFFCBD5E1); // Figma #CBD5E1 (Slate 300)

  // Text Colors
  static const Color textPrimary = Color(0xFF0F172A); // Slate 900
  static const Color textDarkNavy = Color(0xFF00152A); // Deep Navy text
  static const Color textSecondary = Color(0xFF43474D); // Medium Slate
  static const Color textSlate = Color(0xFF334155); // Slate 700
  static const Color textMuted = Color(0xFF64748B); // Slate 500
  static const Color textSubtle = Color(0xFF94A3B8); // Slate 400

  // Status Badge Colors (Figma Specific)
  static const Color statusDiajukan = Color(0xFF0051D5);
  static const Color statusDiajukanBg = Color(0xFFEFF6FF);
  static const Color statusRevisi = Color(0xFFDC2626);
  static const Color statusRevisiBg = Color(0xFFFEE2E2);
  static const Color statusMenunggu = Color(0xFFB45309);
  static const Color statusMenungguBg = Color(0xFFFEF3C7);
  static const Color statusDisetujui = Color(0xFF10B981);
  static const Color statusDisetujuiBg = Color(0xFFECFDF5);
  static const Color statusSelesai = Color(0xFF059669);
  static const Color statusSelesaiBg = Color(0xFFDCFCE7);
  static const Color statusDitolak = Color(0xFF64748B);
  static const Color statusDitolakBg = Color(0xFFF1F5F9);
  static const Color statusSiapDiambil = Color(0xFF0284C7);
  static const Color statusSiapDiambilBg = Color(0xFFE0F2FE);

  // Chat Bubbles
  static const Color chatBubbleBot = Color(0xFFFFFFFF);
  static const Color chatBubbleUser = Color(0xFF2563EB);
}
