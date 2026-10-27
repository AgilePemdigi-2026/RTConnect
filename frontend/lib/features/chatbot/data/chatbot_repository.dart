import '../../../core/network/api_client.dart';
import '../../../core/network/api_endpoints.dart';

class ChatbotRepository {
  final ApiClient _apiClient;

  ChatbotRepository({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  Future<Map<String, dynamic>> sendQuery({
    required String query,
    int? sessionId,
  }) async {
    final response = await _apiClient.dio.post<Map<String, dynamic>>(
      ApiEndpoints.chatbotQuery,
      data: {
        'query': query,
        if (sessionId != null) 'session_id': sessionId,
      },
    );
    return Map<String, dynamic>.from(response.data!['data'] as Map);
  }

  Future<List<Map<String, dynamic>>> getSessions() async {
    final response = await _apiClient.dio.get<Map<String, dynamic>>('/chatbot/sessions');
    final data = response.data!['data'] as List;
    return data.map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  Future<List<Map<String, dynamic>>> getSessionMessages(int sessionId) async {
    final response = await _apiClient.dio.get<Map<String, dynamic>>('/chatbot/sessions/$sessionId/messages');
    final data = response.data!['data'] as List;
    return data.map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }
}
