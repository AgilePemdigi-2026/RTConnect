import 'package:dio/dio.dart';
import '../../../core/network/api_client.dart';
import '../../../core/network/api_endpoints.dart';

class LetterRepository {
  final ApiClient _apiClient;

  LetterRepository({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  Future<List<Map<String, dynamic>>> getLetterTypes() async {
    final response = await _apiClient.dio.get<Map<String, dynamic>>(ApiEndpoints.letterTypes);
    final data = response.data!['data'] as List;
    return data.map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  Future<Map<String, dynamic>> applyLetter({
    required int jenisSuratId,
    required String keperluan,
    required String metodeTandaTangan,
    String? lampiranPath,
    Map<String, String> dataPemohon = const {},
  }) async {
    // dataPemohon: pekerjaan, jenis_kelamin, tempat_lahir, tanggal_lahir (YYYY-MM-DD),
    // agama, status_kawin, kewarganegaraan, nomor_kk, tujuan, keterangan_lain
    dynamic payload;
    if (lampiranPath != null && lampiranPath.isNotEmpty) {
      payload = FormData.fromMap({
        'jenis_surat_id': jenisSuratId,
        'keperluan': keperluan,
        'metode_tanda_tangan': metodeTandaTangan,
        ...dataPemohon,
        'lampiran': await MultipartFile.fromFile(lampiranPath),
      });
    } else {
      payload = {
        'jenis_surat_id': jenisSuratId,
        'keperluan': keperluan,
        'metode_tanda_tangan': metodeTandaTangan,
        ...dataPemohon,
      };
    }

    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      ApiEndpoints.applyLetter,
      data: payload,
    );
    return Map<String, dynamic>.from(response.data!['data'] as Map);
  }

  /// Data pemohon dari pengajuan terakhir (null bila belum pernah mengajukan).
  Future<Map<String, dynamic>?> getMyLastApplicantData() async {
    final response = await _apiClient.dio.get<Map<String, dynamic>>(ApiEndpoints.myLastApplicantData);
    final data = response.data!['data'];
    return data == null ? null : Map<String, dynamic>.from(data as Map);
  }

  /// Asisten AI: isi formulir dari cerita warga (biodata tersimpan dipakai ulang).
  Future<Map<String, dynamic>> aiFill(String pesan) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      ApiEndpoints.aiFill,
      data: {'pesan': pesan},
      // Gemini bisa butuh lebih lama dari batas default 15 detik.
      options: Options(receiveTimeout: const Duration(seconds: 90)),
    );
    return Map<String, dynamic>.from(response.data!['data'] as Map);
  }

  Future<List<Map<String, dynamic>>> getMyApplications() async {
    final response = await _apiClient.dio.get<Map<String, dynamic>>(ApiEndpoints.myApplications);
    final data = response.data!['data'] as List;
    return data.map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  Future<List<Map<String, dynamic>>> getIncomingQueue() async {
    final response = await _apiClient.dio.get<Map<String, dynamic>>(ApiEndpoints.incomingQueue);
    final data = response.data!['data'] as List;
    return data.map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  Future<Map<String, dynamic>> getApplicationDetail(int id) async {
    final response = await _apiClient.dio.get<Map<String, dynamic>>(ApiEndpoints.letterDetail(id));
    return Map<String, dynamic>.from(response.data!['data'] as Map);
  }

  Future<void> resubmitLetter(int id, String keperluan) async {
    await _apiClient.dio.put<Map<String, dynamic>>(
      ApiEndpoints.resubmitLetter(id),
      data: {'keperluan': keperluan},
    );
  }

  Future<Map<String, dynamic>> submitDecision(int id, String action, String catatan) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      ApiEndpoints.letterDecision(id),
      data: {
        'action': action,
        'catatan': catatan,
      },
    );
    return Map<String, dynamic>.from(response.data!['data'] as Map);
  }

  Future<Map<String, dynamic>> signDigital(int id, String pin) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      ApiEndpoints.signDigital(id),
      data: {'pin': pin},
    );
    return Map<String, dynamic>.from(response.data!['data'] as Map);
  }

  Future<void> confirmPhysical(int id) async {
    await _apiClient.dio.post<Map<String, dynamic>>(ApiEndpoints.confirmPhysical(id));
  }
}
