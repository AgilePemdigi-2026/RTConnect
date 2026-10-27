import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_picker/file_picker.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/router/route_names.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_typography.dart';
import '../../../shared/widgets/rt_primary_button.dart';
import '../../../shared/widgets/rt_text_field.dart';
import '../domain/auth_validators.dart';
import 'auth_controller.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();

  final _nikController = TextEditingController();
  final _namaController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _phoneController = TextEditingController();
  final _alamatController = TextEditingController();

  String? _selectedSignaturePath;
  String? _signatureFileName;

  final _confirmPasswordController = TextEditingController();

  @override
  void dispose() {
    _nikController.dispose();
    _namaController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _phoneController.dispose();
    _alamatController.dispose();
    super.dispose();
  }

  Future<void> _pickSignatureFile() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['png', 'jpg', 'jpeg'],
    );

    if (result != null && result.files.single.path != null) {
      setState(() {
        _selectedSignaturePath = result.files.single.path;
        _signatureFileName = result.files.single.name;
      });
    }
  }

  Future<void> _submitRegister() async {
    if (!_formKey.currentState!.validate()) return;

    if (_passwordController.text != _confirmPasswordController.text) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          backgroundColor: AppColors.error,
          content: Text('Konfirmasi kata sandi tidak cocok'),
        ),
      );
      return;
    }

    final success = await ref.read(authControllerProvider.notifier).register(
      nik: _nikController.text.trim(),
      namaLengkap: _namaController.text.trim(),
      email: _emailController.text.trim(),
      password: _passwordController.text.trim(),
      nomorTelepon: _phoneController.text.trim(),
      alamat: _alamatController.text.trim(),
      signaturePath: _selectedSignaturePath,
    );

    if (mounted) {
      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            backgroundColor: AppColors.success,
            content: Text('Registrasi berhasil! Silakan masuk dengan akun Anda.'),
          ),
        );
        context.go(RouteNames.login);
      } else {
        final error = ref.read(authControllerProvider).errorMessage ?? 'Gagal mendaftar';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            backgroundColor: AppColors.error,
            content: Text(error),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authControllerProvider);

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded, color: AppColors.textPrimary),
          onPressed: () => context.go(RouteNames.login),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 8.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              // Header Title: Registrasi Akun (Figma #69:3928)
              Text(
                'Registrasi Akun',
                style: AppTypography.displayLarge.copyWith(
                  fontSize: 28,
                  fontWeight: FontWeight.w700,
                  color: AppColors.navyDeep,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                'Daftarkan diri Anda sebagai warga ${AppConstants.rtArea}',
                textAlign: TextAlign.center,
                style: AppTypography.bodySmall.copyWith(color: AppColors.textMuted),
              ),
              const SizedBox(height: 24),

              // Form Container Box matching Figma #69:3895 (fill #EDF0FF, 16px radius)
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
                      // 1. NIK Field with Counter and Helper Text (Figma #69:4027)
                      RTTextField(
                        label: 'NIK',
                        hint: '3515082104990001',
                        isRequired: true,
                        controller: _nikController,
                        keyboardType: TextInputType.number,
                        counterText: '${_nikController.text.length}/16',
                        helperText: 'Pastikan NIK sesuai dengan KTP elektronik.',
                        validator: AuthValidators.validateNik,
                        onChanged: (val) => setState(() {}),
                        prefixIcon: const Icon(
                          Icons.badge_outlined,
                          size: 20,
                          color: AppColors.textSubtle,
                        ),
                      ),
                      const SizedBox(height: 14),

                      // 2. Nama Lengkap (Figma #69:4046)
                      RTTextField(
                        label: 'Nama Lengkap',
                        hint: 'Nama lengkap sesuai KTP',
                        isRequired: true,
                        controller: _namaController,
                        validator: (v) =>
                            (v == null || v.trim().isEmpty) ? 'Nama lengkap wajib diisi' : null,
                        prefixIcon: const Icon(
                          Icons.person_outline_rounded,
                          size: 20,
                          color: AppColors.textSubtle,
                        ),
                      ),
                      const SizedBox(height: 14),

                      // 3. Alamat Lengkap (Figma #69:4057)
                      RTTextField(
                        label: 'Alamat Lengkap',
                        hint: 'Contoh: Griya Taman Asri Blok B No. 12',
                        isRequired: true,
                        controller: _alamatController,
                        maxLines: 2,
                        validator: (v) =>
                            (v == null || v.trim().isEmpty) ? 'Alamat wajib diisi' : null,
                        prefixIcon: const Icon(
                          Icons.location_on_outlined,
                          size: 20,
                          color: AppColors.textSubtle,
                        ),
                      ),
                      const SizedBox(height: 14),

                      // 4. Nomor WhatsApp / Telepon (Figma #69:4067)
                      RTTextField(
                        label: 'Nomor WhatsApp / Telepon',
                        hint: '081234567890',
                        isRequired: true,
                        controller: _phoneController,
                        keyboardType: TextInputType.phone,
                        validator: AuthValidators.validatePhone,
                        prefixIcon: const Icon(
                          Icons.phone_android_rounded,
                          size: 20,
                          color: AppColors.textSubtle,
                        ),
                      ),
                      const SizedBox(height: 14),

                      // 5. Email (Figma #69:4080)
                      RTTextField(
                        label: 'Alamat Email',
                        hint: 'warga@email.com',
                        isRequired: true,
                        controller: _emailController,
                        keyboardType: TextInputType.emailAddress,
                        validator: AuthValidators.validateEmail,
                        prefixIcon: const Icon(
                          Icons.mail_outline_rounded,
                          size: 20,
                          color: AppColors.textSubtle,
                        ),
                      ),
                      const SizedBox(height: 14),

                      // 6. Kata Sandi (Figma #69:4092)
                      RTTextField(
                        label: 'Kata Sandi',
                        hint: 'Minimal 12 karakter',
                        isRequired: true,
                        controller: _passwordController,
                        isPassword: true,
                        validator: AuthValidators.validateNewPassword,
                        prefixIcon: const Icon(
                          Icons.lock_outline_rounded,
                          size: 20,
                          color: AppColors.textSubtle,
                        ),
                      ),
                      const SizedBox(height: 14),

                      // 7. Konfirmasi Kata Sandi (Figma #69:4103)
                      RTTextField(
                        label: 'Konfirmasi Kata Sandi',
                        hint: 'Ulangi kata sandi Anda',
                        isRequired: true,
                        controller: _confirmPasswordController,
                        isPassword: true,
                        validator: (v) =>
                            (v != _passwordController.text) ? 'Kata sandi tidak cocok' : null,
                        prefixIcon: const Icon(
                          Icons.lock_outline_rounded,
                          size: 20,
                          color: AppColors.textSubtle,
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Optional Signature Scan upload container
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: AppColors.borderSubtle, width: 1),
                        ),
                        child: Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(
                                color: AppColors.primaryBg,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: const Icon(
                                Icons.draw_outlined,
                                color: AppColors.primaryBrand,
                                size: 20,
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'Pindaian TTD (Opsional)',
                                    style: AppTypography.labelBold.copyWith(fontSize: 12),
                                  ),
                                  Text(
                                    _signatureFileName ?? 'Format PNG/JPG di kertas putih',
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                    style: AppTypography.caption.copyWith(fontSize: 10),
                                  ),
                                ],
                              ),
                            ),
                            TextButton(
                              onPressed: _pickSignatureFile,
                              style: TextButton.styleFrom(
                                padding: const EdgeInsets.symmetric(horizontal: 10),
                              ),
                              child: Text(
                                _signatureFileName != null ? 'Ganti' : 'Unggah',
                                style: const TextStyle(fontWeight: FontWeight.bold),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 24),

              // Register Button matching Figma #69:4132
              RTPrimaryButton(
                text: 'Register',
                trailingIcon: Icons.arrow_forward_rounded,
                height: 52,
                borderRadius: 12,
                isLoading: authState.isLoading,
                onPressed: _submitRegister,
              ),

              const SizedBox(height: 20),

              // Footer: Sudah memiliki akun warga? Masuk di sini (Figma #69:3966)
              TextButton(
                onPressed: () => context.go(RouteNames.login),
                child: RichText(
                  text: TextSpan(
                    text: 'Sudah memiliki akun warga? ',
                    style: AppTypography.bodyMedium.copyWith(
                      color: AppColors.textMuted,
                      fontSize: 13,
                    ),
                    children: [
                      TextSpan(
                        text: 'Masuk di sini',
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
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }
}
