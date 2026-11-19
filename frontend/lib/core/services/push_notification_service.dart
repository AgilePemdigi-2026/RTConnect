import 'dart:async';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import '../network/api_client.dart';
import '../network/api_endpoints.dart';
import '../router/app_router.dart';
import '../router/route_names.dart';

/// Top-level background message handler wajib bersifat static / top-level
/// dengan anotasi @pragma('vm:entry-point').
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  try {
    await Firebase.initializeApp();
  } catch (e) {
    debugPrint('[FCM Background] Inisialisasi Firebase gagal: $e');
  }
  debugPrint('[FCM Background] Pesan diterima: ${message.messageId} - ${message.notification?.title}');
}

class PushNotificationService {
  static final FirebaseMessaging _messaging = FirebaseMessaging.instance;
  static final FlutterLocalNotificationsPlugin _localNotifications = FlutterLocalNotificationsPlugin();
  
  static const String _channelId = 'rtconnect_high_importance_channel';
  static const String _channelName = 'Notifikasi RTConnect';
  static const String _channelDescription = 'Kanal notifikasi penting untuk surat pengantar dan administrasi RT';

  static const AndroidNotificationChannel _androidChannel = AndroidNotificationChannel(
    _channelId,
    _channelName,
    description: _channelDescription,
    importance: Importance.max,
    playSound: true,
  );

  static bool _isInitialized = false;
  static StreamSubscription<String>? _tokenRefreshSub;

  /// Inisialisasi Firebase Core, Foreground & Background Notification Handlers
  static Future<void> initialize() async {
    if (_isInitialized) return;

    try {
      await Firebase.initializeApp();
    } catch (e) {
      debugPrint('[FCM] Firebase.initializeApp dilewati/gagal (mungkin di platform web/desktop tanpa config): $e');
      return;
    }

    // Set background message handler
    FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);

    // Setup Local Notifications untuk platform Android (memunculkan banner saat aplikasi di foreground)
    if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) {
      const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
      const initSettings = InitializationSettings(android: androidSettings);

      await _localNotifications.initialize(
        initSettings,
        onDidReceiveNotificationResponse: (NotificationResponse response) {
          if (response.payload != null && response.payload!.isNotEmpty) {
            _navigateToTarget(response.payload!);
          }
        },
      );

      final androidPlugin = _localNotifications.resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin>();
      if (androidPlugin != null) {
        await androidPlugin.createNotificationChannel(_androidChannel);
      }
    }

    // Konfigurasi opsi presentasi notifikasi saat aplikasi berada di Foreground
    await _messaging.setForegroundNotificationPresentationOptions(
      alert: true,
      badge: true,
      sound: true,
    );

    // Dengarkan pesan masuk saat aplikasi sedang dibuka (Foreground)
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      debugPrint('[FCM Foreground] Pesan masuk: ${message.notification?.title} - ${message.notification?.body}');
      _showLocalNotification(message);
    });

    // Tangani interaksi klik notifikasi saat aplikasi berada di Background (minimized)
    FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
      debugPrint('[FCM Tap Background] Pengguna menekan notifikasi: ${message.data}');
      _handleNotificationPayload(message.data);
    });

    // Periksa apakah aplikasi dibuka dari kondisi mati (Terminated) melalui tap notifikasi
    final initialMessage = await _messaging.getInitialMessage();
    if (initialMessage != null) {
      debugPrint('[FCM Tap Terminated] Aplikasi dibuka via notifikasi: ${initialMessage.data}');
      // Berikan jeda sedikit agar GoRouter siap
      Future.delayed(const Duration(milliseconds: 600), () {
        _handleNotificationPayload(initialMessage.data);
      });
    }

    _isInitialized = true;
    debugPrint('[FCM] PushNotificationService berhasil diinisialisasi.');
  }

  /// Meminta izin notifikasi (wajib untuk Android 13+ / iOS)
  static Future<bool> requestPermission() async {
    try {
      final settings = await _messaging.requestPermission(
        alert: true,
        announcement: false,
        badge: true,
        carPlay: false,
        criticalAlert: false,
        provisional: false,
        sound: true,
      );

      final isGranted = settings.authorizationStatus == AuthorizationStatus.authorized ||
          settings.authorizationStatus == AuthorizationStatus.provisional;
      debugPrint('[FCM] Status izin notifikasi: ${settings.authorizationStatus}');
      return isGranted;
    } catch (e) {
      debugPrint('[FCM] Gagal meminta izin notifikasi: $e');
      return false;
    }
  }

  /// Mengambil FCM Device Token dan menyinkronkannya ke Backend Flask
  static Future<void> syncDeviceToken(ApiClient apiClient) async {
    final granted = await requestPermission();
    if (!granted) {
      debugPrint('[FCM] Pengguna menolak izin notifikasi, token tidak disinkronkan.');
      return;
    }

    try {
      final token = await _messaging.getToken();
      if (token != null && token.isNotEmpty) {
        debugPrint('[FCM] Token perangkat diperoleh: ${token.substring(0, 15)}...');
        await _sendTokenToBackend(apiClient, token);
      }

      // Dengarkan jika ada regenerasi token dari Firebase
      _tokenRefreshSub?.cancel();
      _tokenRefreshSub = _messaging.onTokenRefresh.listen((newToken) async {
        debugPrint('[FCM] Token perangkat diperbarui oleh Firebase: ${newToken.substring(0, 15)}...');
        await _sendTokenToBackend(apiClient, newToken);
      });
    } catch (e) {
      debugPrint('[FCM] Gagal mengambil/mengirim FCM token: $e');
    }
  }

  /// Menghapus token dari backend saat pengguna melakukan logout
  static Future<void> removeDeviceToken(ApiClient apiClient) async {
    try {
      _tokenRefreshSub?.cancel();
      _tokenRefreshSub = null;
      await apiClient.dio.delete(ApiEndpoints.deviceToken);
      debugPrint('[FCM] Token perangkat berhasil dihapus dari backend.');
    } catch (e) {
      debugPrint('[FCM] Gagal menghapus token perangkat dari backend: $e');
    }
  }

  static Future<void> _sendTokenToBackend(ApiClient apiClient, String token) async {
    try {
      await apiClient.dio.post(
        ApiEndpoints.deviceToken,
        data: {'fcm_token': token},
      );
      debugPrint('[FCM] Token perangkat berhasil disimpan ke backend database.');
    } catch (e) {
      debugPrint('[FCM] Gagal menyimpan token ke backend: $e');
    }
  }

  /// Memunculkan notifikasi banner (Heads-up) lokal saat aplikasi di Foreground
  static void _showLocalNotification(RemoteMessage message) {
    final notification = message.notification;
    if (notification == null) return;

    final pengajuanId = message.data['pengajuan_id'] ?? '';
    final tautan = message.data['tautan'] ?? (pengajuanId.isNotEmpty ? '/letters/$pengajuanId' : '');

    _localNotifications.show(
      notification.hashCode,
      notification.title ?? 'Notifikasi RTConnect',
      notification.body ?? '',
      NotificationDetails(
        android: AndroidNotificationDetails(
          _androidChannel.id,
          _androidChannel.name,
          channelDescription: _androidChannel.description,
          importance: Importance.max,
          priority: Priority.high,
          icon: '@mipmap/ic_launcher',
          playSound: true,
        ),
      ),
      payload: tautan,
    );
  }

  /// Menangani payload data notifikasi saat notifikasi ditekan
  static void _handleNotificationPayload(Map<String, dynamic> data) {
    final pengajuanId = data['pengajuan_id']?.toString() ?? '';
    final tautan = data['tautan']?.toString() ?? '';

    if (pengajuanId.isNotEmpty) {
      _navigateToTarget('/letters/$pengajuanId');
    } else if (tautan.isNotEmpty) {
      _navigateToTarget(tautan);
    } else {
      _navigateToTarget(RouteNames.notifications);
    }
  }

  static void _navigateToTarget(String path) {
    try {
      appRouter.push(path);
    } catch (e) {
      debugPrint('[FCM Navigation] Gagal navigasi ke $path: $e');
      try {
        appRouter.push(RouteNames.notifications);
      } catch (_) {}
    }
  }
}
