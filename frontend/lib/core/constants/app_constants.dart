import 'package:flutter/foundation.dart';

/// Application-wide constants for RTConnect
class AppConstants {
  static const String appName = 'RTConnect';
  static const String rtArea = String.fromEnvironment(
    'RT_AREA',
    defaultValue: 'RT 032 / RW 08 Griya Taman Asri',
  );
  static String get appTagline => 'Aplikasi Administrasi Warga $rtArea';

  // Override this at build time for the public HTTPS deployment API.
  static const String _buildTimeBaseUrl = String.fromEnvironment('API_BASE_URL');

  // Customizable runtime Base URL (can be changed dynamically in-app)
  static String? customBaseUrl;

  // Local defaults are for development only. Production builds should pass API_BASE_URL.
  static String get defaultBaseUrl {
    if (customBaseUrl != null && customBaseUrl!.isNotEmpty) {
      return customBaseUrl!.replaceFirst(RegExp(r'/+$'), '');
    }
    if (_buildTimeBaseUrl.isNotEmpty) {
      return _buildTimeBaseUrl.replaceFirst(RegExp(r'/+$'), '');
    }
    if (kIsWeb) return 'http://127.0.0.1:5000/api/v1';
    if (kDebugMode && defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:5000/api/v1';
    }
    return 'http://127.0.0.1:5000/api/v1';
  }

  // Secure Storage Keys
  static const String keyAuthToken = 'auth_token';
  static const String keyUserRole = 'user_role';
  static const String keyUserId = 'user_id';
  static const String keyUserNik = 'user_nik';
  static const String keyUserName = 'user_name';
  static const String keyCustomBaseUrl = 'custom_base_url';

}
