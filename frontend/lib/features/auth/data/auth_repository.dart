import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/errors/app_exception.dart';
import '../../../core/network/api_client.dart';
import '../../../core/network/api_endpoints.dart';
import '../domain/user_entity.dart';

class AuthRepository {
  final ApiClient _apiClient;
  final FlutterSecureStorage _storage;

  AuthRepository({
    ApiClient? apiClient,
    FlutterSecureStorage? storage,
  })  : _apiClient = apiClient ?? ApiClient(),
        _storage = storage ?? const FlutterSecureStorage();

  Future<UserEntity> login(String identity, String password) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      ApiEndpoints.login,
      data: {
        'identity': identity,
        'password': password,
      },
    );

    final data = response.data!['data'] as Map<String, dynamic>;
    final token = data['token'] as String;
    final userMap = data['user'] as Map<String, dynamic>;
    final user = UserEntity.fromJson(userMap);

    await _storage.write(key: AppConstants.keyAuthToken, value: token);
    await _storage.write(key: AppConstants.keyUserRole, value: user.role);
    await _storage.write(key: AppConstants.keyUserId, value: user.id.toString());
    await _storage.write(key: AppConstants.keyUserName, value: user.namaLengkap);
    await _storage.write(key: AppConstants.keyUserNik, value: user.nik);

    return user;
  }

  Future<void> register({
    required String nik,
    required String namaLengkap,
    required String email,
    required String password,
    required String nomorTelepon,
    required String alamat,
    String? signaturePath,
  }) async {
    dynamic payload;
    if (signaturePath != null && signaturePath.isNotEmpty) {
      payload = FormData.fromMap({
        'nik': nik,
        'nama_lengkap': namaLengkap,
        'email': email,
        'password': password,
        'nomor_telepon': nomorTelepon,
        'alamat': alamat,
        'tanda_tangan': await MultipartFile.fromFile(
          signaturePath,
          filename: 'signature_$nik.png',
        ),
      });
    } else {
      payload = {
        'nik': nik,
        'nama_lengkap': namaLengkap,
        'email': email,
        'password': password,
        'nomor_telepon': nomorTelepon,
        'alamat': alamat,
      };
    }

    await _apiClient.dio.post<Map<String, dynamic>>(
      ApiEndpoints.register,
      data: payload,
    );
  }

  Future<UserEntity?> getCurrentUser() async {
    final token = await _storage.read(key: AppConstants.keyAuthToken);
    if (token == null) return null;

    try {
      final response = await _apiClient.dio.get<Map<String, dynamic>>(ApiEndpoints.me);
      final data = response.data!['data'] as Map<String, dynamic>;
      return UserEntity.fromJson(data);
    } on DioException catch (error) {
      // A stale token (for example, one signed by an old development key)
      // cannot be refreshed. Clear only authentication data so the saved API
      // server URL remains available for the next login.
      if (error.error is AuthException || error.response?.statusCode == 401) {
        await _clearCredentials();
      }
      return null;
    } catch (_) {
      return null;
    }
  }

  Future<String?> getSavedRole() async {
    return await _storage.read(key: AppConstants.keyUserRole);
  }

  Future<bool> isAuthenticated() async {
    final token = await _storage.read(key: AppConstants.keyAuthToken);
    return token != null && token.isNotEmpty;
  }

  Future<void> logout() async {
    await _clearCredentials();
  }

  Future<void> _clearCredentials() async {
    await Future.wait([
      _storage.delete(key: AppConstants.keyAuthToken),
      _storage.delete(key: AppConstants.keyUserRole),
      _storage.delete(key: AppConstants.keyUserId),
      _storage.delete(key: AppConstants.keyUserName),
      _storage.delete(key: AppConstants.keyUserNik),
    ]);
  }
}
