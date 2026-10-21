/// Base exception class for RTConnect application
class AppException implements Exception {
  final String message;
  final String? code;

  const AppException(this.message, {this.code});

  @override
  String toString() => message;
}

class NetworkException extends AppException {
  const NetworkException([super.message = 'Koneksi jaringan terputus. Silakan coba lagi.'])
      : super(code: 'NETWORK_ERROR');
}

class AuthException extends AppException {
  const AuthException([super.message = 'Email/NIK atau password salah.'])
      : super(code: 'AUTH_ERROR');
}

class ValidationException extends AppException {
  const ValidationException(super.message) : super(code: 'VALIDATION_ERROR');
}

class ServerException extends AppException {
  const ServerException([super.message = 'Terjadi kesalahan pada server.'])
      : super(code: 'SERVER_ERROR');
}
