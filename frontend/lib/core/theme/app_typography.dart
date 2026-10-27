import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'app_colors.dart';

/// Design Tokens: Typography for RTConnect grounded in Plus Jakarta Sans
class AppTypography {
  // Display & Hero Titles
  static TextStyle heroTitle = GoogleFonts.plusJakartaSans(
    fontSize: 30.0,
    fontWeight: FontWeight.w800,
    height: 37.5 / 30.0,
    letterSpacing: -0.75,
    color: AppColors.textPrimary,
  );

  static TextStyle displayLarge = GoogleFonts.plusJakartaSans(
    fontSize: 28.0,
    fontWeight: FontWeight.w700,
    height: 36.4 / 28.0,
    letterSpacing: -0.5,
    color: AppColors.navyDeep,
  );

  static TextStyle titleLarge = GoogleFonts.plusJakartaSans(
    fontSize: 24.0,
    fontWeight: FontWeight.w700,
    height: 32.0 / 24.0,
    letterSpacing: -0.5,
    color: AppColors.textDarkNavy,
  );

  static TextStyle titleMedium = GoogleFonts.plusJakartaSans(
    fontSize: 18.0,
    fontWeight: FontWeight.w700,
    height: 26.0 / 18.0,
    letterSpacing: -0.25,
    color: AppColors.textDarkNavy,
  );

  static TextStyle titleSmall = GoogleFonts.plusJakartaSans(
    fontSize: 16.0,
    fontWeight: FontWeight.w600,
    height: 22.0 / 16.0,
    color: AppColors.textPrimary,
  );

  // Body Styles
  static TextStyle bodyLarge = GoogleFonts.plusJakartaSans(
    fontSize: 14.0,
    fontWeight: FontWeight.w500,
    height: 20.0 / 14.0,
    color: AppColors.textPrimary,
  );

  static TextStyle bodyMedium = GoogleFonts.plusJakartaSans(
    fontSize: 13.0,
    fontWeight: FontWeight.w400,
    height: 18.0 / 13.0,
    color: AppColors.textSecondary,
  );

  static TextStyle bodySmall = GoogleFonts.plusJakartaSans(
    fontSize: 12.0,
    fontWeight: FontWeight.w400,
    height: 16.0 / 12.0,
    color: AppColors.textMuted,
  );

  // Labels & Captions
  static TextStyle labelLarge = GoogleFonts.plusJakartaSans(
    fontSize: 14.0,
    fontWeight: FontWeight.w700,
    height: 20.0 / 14.0,
    color: AppColors.textPrimary,
  );

  static TextStyle labelMedium = GoogleFonts.plusJakartaSans(
    fontSize: 12.0,
    fontWeight: FontWeight.w700,
    height: 16.0 / 12.0,
    color: AppColors.navyHeader,
  );

  static TextStyle labelSmall = GoogleFonts.plusJakartaSans(
    fontSize: 11.0,
    fontWeight: FontWeight.w600,
    height: 16.0 / 11.0,
    letterSpacing: 0.2,
    color: AppColors.textSecondary,
  );

  static TextStyle caption = GoogleFonts.plusJakartaSans(
    fontSize: 11.0,
    fontWeight: FontWeight.w500,
    height: 15.0 / 11.0,
    color: AppColors.textMuted,
  );

  static TextStyle badgeUppercase = GoogleFonts.plusJakartaSans(
    fontSize: 11.0,
    fontWeight: FontWeight.w700,
    height: 16.0 / 11.0,
    letterSpacing: 0.5,
    color: AppColors.primaryBrand,
  );

  static TextStyle buttonLabel = GoogleFonts.plusJakartaSans(
    fontSize: 14.0,
    fontWeight: FontWeight.w700,
    height: 20.0 / 14.0,
    color: Colors.white,
  );

  // Semantic Aliases
  static TextStyle get heading1 => titleLarge;
  static TextStyle get heading2 => titleMedium;
  static TextStyle get heading3 => titleSmall;
  static TextStyle get labelBold => labelMedium;
}
