import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../constants/app_constants.dart';
import '../errors/app_exception.dart';

/// Centralized Dio REST API Client
class ApiClient {
  late final Dio _dio;
  late final String _baseUrl;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  ApiClient({String? baseUrl}) {
    final effectiveBaseUrl = baseUrl ?? AppConstants.defaultBaseUrl;
    _baseUrl = effectiveBaseUrl.replaceFirst(RegExp(r'/+$'), '');
    _dio = Dio(
      BaseOptions(
        baseUrl: effectiveBaseUrl,
        connectTimeout: const Duration(seconds: 10),
        receiveTimeout: const Duration(seconds: 15),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final customUrl = await _storage.read(key: AppConstants.keyCustomBaseUrl);
          final selectedBaseUrl = (customUrl != null && customUrl.isNotEmpty)
              ? customUrl.trim().replaceFirst(RegExp(r'/+$'), '')
              : _baseUrl;
          final uri = Uri.tryParse(selectedBaseUrl);
          if (uri == null || !uri.hasAuthority || !{'http', 'https'}.contains(uri.scheme)) {
            return handler.reject(
              DioException(
                requestOptions: options,
                error: const FormatException('Alamat server API tidak valid.'),
              ),
            );
          }
          if (kReleaseMode && uri.scheme != 'https') {
            return handler.reject(
              DioException(
                requestOptions: options,
                error: const FormatException('Aplikasi release hanya menerima API melalui HTTPS.'),
              ),
            );
          }
          options.baseUrl = selectedBaseUrl;

          final token = await _storage.read(key: AppConstants.keyAuthToken);
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          return handler.next(options);
        },
        onError: (DioException error, handler) async {
          final requestPath = error.requestOptions.path.toLowerCase();
          final isLoginRequest = requestPath.endsWith('/auth/login');
          if (error.response?.statusCode == 401 &&
              !isLoginRequest &&
              _hasBearerToken(error.requestOptions)) {
            await _clearStoredCredentials();
          }
          final exception = _handleDioError(error);
          return handler.reject(
            DioException(
              requestOptions: error.requestOptions,
              error: exception,
              message: exception.message,
            ),
          );
        },
      ),
    );
  }

  Dio get dio => _dio;

  bool _hasBearerToken(RequestOptions options) {
    for (final entry in options.headers.entries) {
      if (entry.key.toLowerCase() == 'authorization' &&
          entry.value is String &&
          (entry.value as String).startsWith('Bearer ')) {
        return true;
      }
    }
    return false;
  }

  Future<void> _clearStoredCredentials() async {
    await Future.wait([
      _storage.delete(key: AppConstants.keyAuthToken),
      _storage.delete(key: AppConstants.keyUserRole),
      _storage.delete(key: AppConstants.keyUserId),
      _storage.delete(key: AppConstants.keyUserName),
      _storage.delete(key: AppConstants.keyUserNik),
    ]);
  }

  AppException _handleDioError(DioException error) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.receiveTimeout:
      case DioExceptionType.connectionError:
        return const NetworkException();
      case DioExceptionType.badResponse:
        final statusCode = error.response?.statusCode;
        final data = error.response?.data;
        final message = (data is Map && data['message'] != null)
            ? data['message'].toString()
            : 'Terjadi kesalahan sistem (${statusCode ?? 500})';

        if (statusCode == 401) {
          return AuthException(message);
        } else if (statusCode == 400) {
          return ValidationException(message);
        }
        return ServerException(message);
      default:
        return AppException(error.message ?? 'Kesalahan tidak terduga');
    }
  }
}
