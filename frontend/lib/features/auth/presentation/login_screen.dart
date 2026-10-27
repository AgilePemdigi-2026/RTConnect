import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/router/route_names.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_typography.dart';
import '../../../shared/widgets/rt_primary_button.dart';
import '../../../shared/widgets/rt_text_field.dart';
import '../domain/auth_validators.dart';
import 'auth_controller.dart';

/// SCREEN-003: Login Page
class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _identifierController = TextEditingController();
  final _passwordController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadSavedServerUrl();
  }

  Future<void> _loadSavedServerUrl() async {
    const storage = FlutterSecureStorage();
    final savedUrl = await storage.read(key: AppConstants.keyCustomBaseUrl);
    if (savedUrl != null && savedUrl.isNotEmpty && mounted) {
      setState(() {
        AppConstants.customBaseUrl = savedUrl;
      });
    }
  }

  @override
  void dispose() {
    _identifierController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    if (!_formKey.currentState!.validate()) return;

    final identity = _identifierController.text.trim();
    final password = _passwordController.text.trim();

    final success = await ref.read(authControllerProvider.notifier).login(identity, password);

    if (mounted) {
      if (success) {
        final user = ref.read(authControllerProvider).user;
        if (user?.role == 'rt') {
          context.go(RouteNames.rtHome);
        } else {
          context.go(RouteNames.wargaHome);
        }
      } else {
        final error = ref.read(authControllerProvider).errorMessage ?? 'Login gagal';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            backgroundColor: AppColors.error,
            content: Text(error),
          ),
        );
      }
    }
  }

  Future<void> _showServerConfigDialog() async {
    const storage = FlutterSecureStorage();
    final savedUrl = await storage.read(key: AppConstants.keyCustomBaseUrl) ?? AppConstants.defaultBaseUrl;
    final controller = TextEditingController(text: savedUrl);

    if (!mounted) return;
    await showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.dns, color: AppColors.primary),
            SizedBox(width: 8),
            Text('Alamat Server API'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Masukkan IP laptop backend (Wi-Fi / Hotspot yang sama):',
              style: AppTypography.bodySmall,
            ),
            const SizedBox(height: AppSpacing.sm),
            TextField(
              controller: controller,
              decoration: const InputDecoration(
                hintText: 'https://api.example.com/api/v1',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Batal'),
          ),
          ElevatedButton(
            onPressed: () async {
              final newUrl = controller.text.trim();
              if (newUrl.isNotEmpty) {
                await storage.write(key: AppConstants.keyCustomBaseUrl, value: newUrl);
                AppConstants.customBaseUrl = newUrl;
                if (ctx.mounted) {
                  Navigator.pop(ctx);
                }
                if (mounted) {
                  setState(() {});
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      backgroundColor: AppColors.success,
                      content: Text('Server disetel ke: $newUrl'),
                    ),
                  );
                }
              }
            },
            child: const Text('Simpan'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authControllerProvider);

    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 20.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                // Brand Header Icon
                Container(
                  width: 64,
                  height: 64,
                  decoration: BoxDecoration(
                    color: AppColors.primaryBg,
                    shape: BoxShape.circle,
                    border: Border.all(color: const Color(0xFFDBEAFE), width: 1.5),
                  ),
                  child: const Center(
                    child: Icon(
                      Icons.account_balance_rounded,
                      size: 32,
                      color: AppColors.primaryBrand,
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // Title: Masuk Akun
                Text(
                  'Masuk Akun',
                  style: AppTypography.displayLarge.copyWith(
                    fontSize: 28,
                    fontWeight: FontWeight.w700,
                    color: AppColors.navyDeep,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'Kelola kebutuhan administrasi RT dalam satu akun',
                  textAlign: TextAlign.center,
                  style: AppTypography.bodySmall.copyWith(color: AppColors.textMuted),
                ),
                const SizedBox(height: 28),

                // Container Form Box matching Figma #69:3881 (fill #EDF0FF, 16px radius)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(20.0),
                  decoration: BoxDecoration(
                    color: AppColors.lightContainer, // Figma #EDF0FF
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: const Color(0xFFD6E0FF), width: 1),
                    boxShadow: const [
                      BoxShadow(
                        color: Color(0x0A000000),
                        blurRadius: 8,
                        offset: Offset(0, 2),
                      ),
                    ],
                  ),
                  child: Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        RTTextField(
                          label: 'Email / NIK',
                          hint: 'Masukkan email atau NIK',
                          isRequired: true,
                          controller: _identifierController,
                          keyboardType: TextInputType.emailAddress,
                          validator: (val) =>
                              AuthValidators.validateRequired(val, 'Email / NIK'),
                          prefixIcon: const Icon(
                            Icons.mail_outline_rounded,
                            size: 20,
                            color: AppColors.textSubtle,
                          ),
                        ),
                        const SizedBox(height: 16),
                        RTTextField(
                          label: 'Kata Sandi',
                          hint: 'Masukkan kata sandi',
                          isRequired: true,
                          controller: _passwordController,
                          isPassword: true,
                          validator: AuthValidators.validatePassword,
                          prefixIcon: const Icon(
                            Icons.lock_outline_rounded,
                            size: 20,
                            color: AppColors.textSubtle,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 24),

                // Button: Masuk ke aplikasi RTConnect (Figma #69:4170)
                RTPrimaryButton(
                  text: 'Masuk ke aplikasi RTConnect',
                  trailingIcon: Icons.arrow_forward_rounded,
                  height: 52,
                  borderRadius: 12,
                  isLoading: authState.isLoading,
                  onPressed: _handleLogin,
                ),

                const SizedBox(height: 20),

                // Footer Link: Register
                TextButton(
                  onPressed: () => context.push(RouteNames.register),
                  child: RichText(
                    text: TextSpan(
                      text: 'Belum memiliki akun warga? ',
                      style: AppTypography.bodyMedium.copyWith(
                        color: AppColors.textMuted,
                        fontSize: 13,
                      ),
                      children: [
                        TextSpan(
                          text: 'Daftar di sini',
                          style: AppTypography.bodyMedium.copyWith(
                            color: AppColors.primaryAction,
                            fontWeight: FontWeight.w700,
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 8),

                // Quick Server Settings Dialog
                TextButton.icon(
                  onPressed: _showServerConfigDialog,
                  icon: const Icon(Icons.dns_outlined, size: 15, color: AppColors.textSubtle),
                  label: Text(
                    'Server API: ${AppConstants.customBaseUrl ?? AppConstants.defaultBaseUrl}',
                    style: AppTypography.caption.copyWith(color: AppColors.textSubtle),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
