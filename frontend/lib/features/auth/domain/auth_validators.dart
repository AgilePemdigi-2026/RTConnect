import 'dart:convert';

/// Domain validation logic for Authentication
class AuthValidators {
  static String? validateNIK(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'NIK wajib diisi';
    }
    final trimmed = value.trim();
    if (!RegExp(r'^\d+$').hasMatch(trimmed)) {
      return 'NIK harus berupa angka';
    }
    if (trimmed.length != 16) {
      return 'NIK harus terdiri dari 16 digit';
    }
    return null;
  }

  /// Alias for backward compatibility
  static String? validateNik(String? value) => validateNIK(value);

  static String? validatePhone(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'Nomor telepon wajib diisi';
    }
    final trimmed = value.trim();
    if (!RegExp(r'^\d+$').hasMatch(trimmed)) {
      return 'Nomor telepon harus berupa angka';
    }
    if (trimmed.length < 10 || trimmed.length > 15) {
      return 'Nomor telepon minimal 10 dan maksimal 15 digit';
    }
    return null;
  }

  static String? validateEmail(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'Email wajib diisi';
    }
    final emailRegex = RegExp(r'^[\w.-]+@([\w-]+\.)+[A-Za-z]{2,63}$');
    if (!emailRegex.hasMatch(value.trim())) {
      return 'Format email tidak valid';
    }
    return null;
  }

  static String? validatePassword(String? value) {
    if (value == null || value.isEmpty) {
      return 'Password wajib diisi';
    }
    if (value.length < 6) {
      return 'Password minimal 6 karakter';
    }
    return null;
  }

  static String? validateNewPassword(String? value) {
    if (value == null || value.isEmpty) {
      return 'Password wajib diisi';
    }
    if (value.length < 12) {
      return 'Password minimal 12 karakter';
    }
    if (utf8.encode(value).length > 72) {
      return 'Password maksimal 72 byte';
    }
    return null;
  }

  static String? validateRequired(String? value, String fieldName) {
    if (value == null || value.trim().isEmpty) {
      return '$fieldName wajib diisi';
    }
    return null;
  }
}
