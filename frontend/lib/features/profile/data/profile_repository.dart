import 'dart:typed_data';
import 'package:dio/dio.dart';
import '../../../core/network/api_client.dart';
import '../../../core/network/api_endpoints.dart';
import '../../auth/domain/user_entity.dart';

class ProfileRepository {
  final ApiClient _apiClient;

  ProfileRepository({ApiClient? apiClient})
      : _apiClient = apiClient ?? ApiClient();

  Future<UserEntity> getProfile() async {
    final response = await _apiClient.dio.get<Map<String, dynamic>>(
      ApiEndpoints.me,
    );
    final data = response.data!['data'] as Map<String, dynamic>;
    return UserEntity.fromJson(data);
  }

  Future<UserEntity> updateProfile({
    required String namaLengkap,
    required String nomorTelepon,
    required String alamat,
    required String email,
  }) async {
    final response = await _apiClient.dio.put<Map<String, dynamic>>(
      ApiEndpoints.updateProfile,
      data: {
        'nama_lengkap': namaLengkap,
        'nomor_telepon': nomorTelepon,
        'alamat': alamat,
        'email': email,
      },
    );
    final data = response.data!['data'] as Map<String, dynamic>;
    return UserEntity.fromJson(data);
  }

  Future<String> updateSignature({
    String? signatureKey,
    String? filePath,
    List<int>? fileBytes,
    String? fileName,
  }) async {
    dynamic payload;
    if (fileBytes != null && fileBytes.isNotEmpty) {
      payload = FormData.fromMap({
        'tanda_tangan': MultipartFile.fromBytes(
          fileBytes,
          filename: fileName ?? 'signature.png',
        ),
      });
    } else if (filePath != null && filePath.isNotEmpty) {
      payload = FormData.fromMap({
        'tanda_tangan': await MultipartFile.fromFile(
          filePath,
          filename: fileName ?? 'signature.png',
        ),
      });
    } else if (signatureKey != null && signatureKey.isNotEmpty) {
      payload = {
        'signature_key': signatureKey,
      };
    } else {
      throw ArgumentError('Tanda tangan tidak valid');
    }

    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      ApiEndpoints.updateSignature,
      data: payload,
    );
    final data = response.data!['data'] as Map<String, dynamic>;
    return data['tanda_tangan_digital']?.toString() ?? '';
  }

  Future<Uint8List?> getSignatureBytes([String? customPath]) async {
    try {
      final endpoint = (customPath != null && customPath.isNotEmpty)
          ? ApiEndpoints.fileUrl(customPath)
          : ApiEndpoints.getSignature;
      final response = await _apiClient.dio.get<List<int>>(
        endpoint,
        options: Options(
          responseType: ResponseType.bytes,
        ),
      );
      if (response.data != null && response.data!.isNotEmpty) {
        return Uint8List.fromList(response.data!);
      }
      return null;
    } catch (_) {
      return null;
    }
  }
}
