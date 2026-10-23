import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../auth/presentation/auth_controller.dart';
import '../data/notification_repository.dart';

final notificationRepositoryProvider = Provider<NotificationRepository>((ref) {
  return NotificationRepository();
});

final notificationsProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final authState = ref.watch(authControllerProvider);
  if (!authState.isAuthenticated) {
    return <String, dynamic>{'unread_count': 0, 'items': <dynamic>[]};
  }

  final repo = ref.watch(notificationRepositoryProvider);
  return await repo.getNotifications();
});

final unreadNotificationCountProvider = Provider<int>((ref) {
  final notifAsync = ref.watch(notificationsProvider);
  return notifAsync.maybeWhen(
    data: (data) => (data['unread_count'] as num?)?.toInt() ?? 0,
    orElse: () => 0,
  );
});
