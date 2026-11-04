import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'route_names.dart';
import '../../features/auth/presentation/auth_controller.dart';
import '../../shared/widgets/rt_bottom_nav_bar.dart';

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
import '../../features/profile/presentation/profile_screen.dart';
import '../../features/profile/presentation/edit_profile_screen.dart';
import '../../features/profile/presentation/signature_screen.dart';

final GlobalKey<NavigatorState> rootNavigatorKey = GlobalKey<NavigatorState>();
final GlobalKey<NavigatorState> shellNavigatorKey = GlobalKey<NavigatorState>();

final GoRouter appRouter = GoRouter(
  navigatorKey: rootNavigatorKey,
  initialLocation: RouteNames.landing,
  routes: [
    // Landing & Auth Routes (Outside Shell)
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

    // Authenticated Shell with Persistent Stateless Bottom Navigation Bar (Primary Tabs ONLY)
    ShellRoute(
      navigatorKey: shellNavigatorKey,
      builder: (context, state, child) {
        return _AuthGate(
          child: _MainNavigationShell(
            currentLocation: state.matchedLocation,
            child: child,
          ),
        );
      },
      routes: [
        // Warga Primary Tabs
        GoRoute(
          path: RouteNames.wargaHome,
          builder: (context, state) => const WargaHomeScreen(),
        ),
        GoRoute(
          path: RouteNames.wargaPengajuan,
          builder: (context, state) => const LetterHistoryScreen(),
        ),

        // RT Primary Tabs
        GoRoute(
          path: RouteNames.rtHome,
          builder: (context, state) => const RTHomeScreen(),
        ),
        GoRoute(
          path: RouteNames.rtQueue,
          builder: (context, state) => const RTReviewScreen(),
        ),

        // Chatbot Tab
        GoRoute(
          path: RouteNames.chatbot,
          builder: (context, state) => const ChatbotScreen(),
        ),
      ],
    ),

    // Sub-screens & Detail Pages (Outside Shell, Root Navigator, No Bottom Nav Bar)
    GoRoute(
      parentNavigatorKey: rootNavigatorKey,
      path: RouteNames.wargaPengajuanBaru,
      builder: (context, state) =>
          const _AuthGate(child: LetterApplicationScreen()),
    ),
    GoRoute(
      parentNavigatorKey: rootNavigatorKey,
      path: '/letters/:id',
      builder: (context, state) {
        final id = int.tryParse(state.pathParameters['id'] ?? '0') ?? 0;
        return _AuthGate(child: LetterDetailScreen(applicationId: id));
      },
    ),
    GoRoute(
      parentNavigatorKey: rootNavigatorKey,
      path: RouteNames.profile,
      builder: (context, state) => const _AuthGate(child: ProfileScreen()),
    ),
    GoRoute(
      parentNavigatorKey: rootNavigatorKey,
      path: RouteNames.editProfile,
      builder: (context, state) => const _AuthGate(child: EditProfileScreen()),
    ),
    GoRoute(
      parentNavigatorKey: rootNavigatorKey,
      path: RouteNames.signature,
      builder: (context, state) => const _AuthGate(child: SignatureScreen()),
    ),
    GoRoute(
      parentNavigatorKey: rootNavigatorKey,
      path: RouteNames.notifications,
      builder: (context, state) =>
          const _AuthGate(child: NotificationFeedScreen()),
    ),
    GoRoute(
      parentNavigatorKey: rootNavigatorKey,
      path: '/surat/preview/:id',
      builder: (context, state) {
        final id = int.tryParse(state.pathParameters['id'] ?? '0') ?? 0;
        return _AuthGate(child: PdfViewerScreen(applicationId: id));
      },
    ),
  ],
);

/// Persistent Shell hosting the stateless Bottom Navigation Bar for primary tabs
class _MainNavigationShell extends ConsumerWidget {
  final String currentLocation;
  final Widget child;

  const _MainNavigationShell({
    required this.currentLocation,
    required this.child,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authControllerProvider);
    final user = authState.user;
    final isRT = user?.isRT ?? false;

    // Calculate active tab index: 0 = Pengajuan, 1 = Beranda, 2 = TanyaRT
    int currentIndex = 1;
    if (currentLocation == RouteNames.wargaPengajuan ||
        currentLocation == RouteNames.rtQueue) {
      currentIndex = 0;
    } else if (currentLocation == RouteNames.chatbot) {
      currentIndex = 2;
    } else {
      currentIndex = 1;
    }

    return Scaffold(
      body: child,
      bottomNavigationBar: RTBottomNavBar(
        currentIndex: currentIndex,
        onTap: (index) {
          if (index == 0) {
            context.go(isRT ? RouteNames.rtQueue : RouteNames.wargaPengajuan);
          } else if (index == 1) {
            context.go(isRT ? RouteNames.rtHome : RouteNames.wargaHome);
          } else if (index == 2) {
            context.go(RouteNames.chatbot);
          }
        },
      ),
    );
  }
}

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
