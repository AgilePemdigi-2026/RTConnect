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

    // Authenticated Shell with Persistent Stateless Bottom Navigation Bar
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
        // Warga Routes
        GoRoute(
          path: RouteNames.wargaHome,
          builder: (context, state) => const WargaHomeScreen(),
        ),
        GoRoute(
          path: RouteNames.wargaPengajuan,
          builder: (context, state) => const LetterHistoryScreen(),
        ),
        GoRoute(
          path: RouteNames.wargaPengajuanBaru,
          builder: (context, state) => const LetterApplicationScreen(),
        ),
        GoRoute(
          path: '/letters/:id',
          builder: (context, state) {
            final id = int.tryParse(state.pathParameters['id'] ?? '0') ?? 0;
            return LetterDetailScreen(applicationId: id);
          },
        ),

        // RT Routes
        GoRoute(
          path: RouteNames.rtHome,
          builder: (context, state) => const RTHomeScreen(),
        ),
        GoRoute(
          path: RouteNames.rtQueue,
          builder: (context, state) => const RTReviewScreen(),
        ),

        // Shared Profile & Signature Routes
        GoRoute(
          path: RouteNames.profile,
          builder: (context, state) => const ProfileScreen(),
        ),
        GoRoute(
          path: RouteNames.editProfile,
          builder: (context, state) => const EditProfileScreen(),
        ),
        GoRoute(
          path: RouteNames.signature,
          builder: (context, state) => const SignatureScreen(),
        ),

        // Chatbot & Notifications
        GoRoute(
          path: RouteNames.chatbot,
          builder: (context, state) => const ChatbotScreen(),
        ),
        GoRoute(
          path: RouteNames.notifications,
          builder: (context, state) => const NotificationFeedScreen(),
        ),

        // PDF Preview
        GoRoute(
          path: '/surat/preview/:id',
          builder: (context, state) {
            final id = int.tryParse(state.pathParameters['id'] ?? '0') ?? 0;
            return PdfViewerScreen(applicationId: id);
          },
        ),
      ],
    ),
  ],
);

/// Persistent Shell hosting the stateless Bottom Navigation Bar
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
    int currentIndex = -1;
    if (currentLocation.startsWith('/warga/pengajuan') ||
        currentLocation.startsWith('/rt/pengajuan') ||
        currentLocation.startsWith('/letters')) {
      currentIndex = 0;
    } else if (currentLocation == RouteNames.wargaHome ||
        currentLocation == RouteNames.rtHome) {
      currentIndex = 1;
    } else if (currentLocation == RouteNames.chatbot) {
      currentIndex = 2;
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
