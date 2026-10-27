import '../../../core/network/api_client.dart';
import '../../../core/network/api_endpoints.dart';

class NotificationRepository {
  final ApiClient _apiClient;

  NotificationRepository({ApiClient? apiClient})
      : _apiClient = apiClient ?? ApiClient();

  Future<Map<String, dynamic>> getNotifications() async {
    final response = await _apiClient.dio.get<Map<String, dynamic>>(
      ApiEndpoints.notifications,
    );
    return Map<String, dynamic>.from(response.data?['data'] as Map? ?? {});
  }

  Future<void> markAsRead(int notificationId, {bool isDibaca = true}) async {
    await _apiClient.dio.put<Map<String, dynamic>>(
      '/notifications/$notificationId/read',
      data: {'is_dibaca': isDibaca},
    );
  }

  Future<void> markAllAsRead() async {
    await _apiClient.dio.put<Map<String, dynamic>>('/notifications/read-all');
  }
}
