import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'route_names.dart';
import '../../features/auth/presentation/auth_controller.dart';

// Screens Import
import '../../features/auth/presentation/landing_screen.dart';
import '../../features/auth/presentation/login_screen.dart';
import '../../features/auth/presentation/register_screen.dart';
import '../../features/home/presentation/warga_home_screen.dart';
import '../../features/home/presentation/rt_home_screen.dart';
import '../../features/letters/presentation/letter_application_screen.dart';
import '../../features/letters/presentation/letter_history_screen.dart';
import '../../features/letters/presentation/letter_detail_screen.dart';
import '../../features/letters/presentation/rt_review_screen.dart';
import '../../features/letters/presentation/pdf_viewer_screen.dart';
import '../../features/chatbot/presentation/chatbot_screen.dart';
import '../../features/notifications/presentation/notification_feed_screen.dart';

final GlobalKey<NavigatorState> rootNavigatorKey = GlobalKey<NavigatorState>();

final GoRouter appRouter = GoRouter(
  navigatorKey: rootNavigatorKey,
  initialLocation: RouteNames.landing,
  routes: [
    // Landing & Auth
    GoRoute(
      path: RouteNames.landing,
      builder: (context, state) => const LandingScreen(),
    ),
    GoRoute(
      path: RouteNames.login,
      builder: (context, state) => const LoginScreen(),
    ),
    GoRoute(
      path: RouteNames.register,
      builder: (context, state) => const RegisterScreen(),
    ),

    // Warga Routes
    GoRoute(
      path: RouteNames.wargaHome,
      builder: (context, state) => const _AuthGate(child: WargaHomeScreen()),
    ),
    GoRoute(
      path: RouteNames.wargaPengajuan,
      builder: (context, state) =>
          const _AuthGate(child: LetterHistoryScreen()),
    ),
    GoRoute(
      path: RouteNames.wargaPengajuanBaru,
      builder: (context, state) =>
          const _AuthGate(child: LetterApplicationScreen()),
    ),
    GoRoute(
      path: '/letters/:id',
      builder: (context, state) {
        final id = int.tryParse(state.pathParameters['id'] ?? '0') ?? 0;
        return _AuthGate(child: LetterDetailScreen(applicationId: id));
      },
    ),

    // RT Routes
    GoRoute(
      path: RouteNames.rtHome,
      builder: (context, state) => const _AuthGate(child: RTHomeScreen()),
    ),
    GoRoute(
      path: RouteNames.rtQueue,
      builder: (context, state) => const _AuthGate(child: RTReviewScreen()),
    ),

    // PDF Preview
    GoRoute(
      path: '/surat/preview/:id',
      builder: (context, state) {
        final id = int.tryParse(state.pathParameters['id'] ?? '0') ?? 0;
        return _AuthGate(child: PdfViewerScreen(applicationId: id));
      },
    ),

    // Chatbot & Notifications
    GoRoute(
      path: RouteNames.chatbot,
      builder: (context, state) => const _AuthGate(child: ChatbotScreen()),
    ),
    GoRoute(
      path: RouteNames.notifications,
      builder: (context, state) =>
          const _AuthGate(child: NotificationFeedScreen()),
    ),
  ],
);

class _AuthGate extends ConsumerWidget {
  final Widget child;

  const _AuthGate({required this.child});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authControllerProvider);
    if (authState.isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    if (!authState.isAuthenticated) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (context.mounted) context.go(RouteNames.login);
      });
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    return child;
  }
}
