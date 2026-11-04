import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/router/route_names.dart';
import '../../../core/theme/app_typography.dart';
import '../../auth/presentation/auth_controller.dart';

/// Screen: Profile Page (Grounded in Figma Node #184:1312 & #186:1175)
class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authControllerProvider);
    final user = authState.user;
    final isRT = user?.isRT ?? false;

    final namaLengkap = user?.namaLengkap ?? (isRT ? 'Ketua RT' : 'Warga RT 04');
    final sapaan = namaLengkap.split(' ').first;
    final nik = user?.nik ?? '-';
    final noTelp = user?.nomorTelepon ?? '-';
    final email = user?.email ?? '-';
    final alamat = (user?.alamat != null && user!.alamat!.isNotEmpty)
        ? user.alamat!
        : 'RT 04 / RW 09, Gunungsari Indah';

    return Scaffold(
      backgroundColor: const Color(0xFFF7F9FB),
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(64.0),
        child: Container(
          decoration: const BoxDecoration(
            color: Colors.white,
            border: Border(
              bottom: BorderSide(color: Color(0xFFECEEF0), width: 1.0),
            ),
          ),
          child: SafeArea(
            bottom: false,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
              child: Row(
                children: [
                  InkWell(
                    onTap: () {
                      if (Navigator.canPop(context)) {
                        Navigator.pop(context);
                      } else {
                        context.go(isRT ? RouteNames.rtHome : RouteNames.wargaHome);
                      }
                    },
                    borderRadius: BorderRadius.circular(8.0),
                    child: Container(
                      width: 36,
                      height: 40,
                      alignment: Alignment.center,
                      child: const Icon(
                        Icons.arrow_back_rounded,
                        color: Color(0xFF00152A),
                        size: 20,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'Profil Saya',
                    style: AppTypography.heading3.copyWith(
                      color: const Color(0xFF00152A),
                      fontSize: 18.0,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 1. Ringkasan Profil Card
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16.0),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16.0),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0x06000000),
                    blurRadius: 10,
                    offset: Offset(0, 2),
                  ),
                ],
              ),
              child: Column(
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      // Avatar
                      Container(
                        width: 64,
                        height: 64,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: const Color(0xFF0051D5).withValues(alpha: 0.1),
                          border: Border.all(
                            color: const Color(0xFF0051D5).withValues(alpha: 0.2),
                            width: 2.0,
                          ),
                        ),
                        child: Center(
                          child: Text(
                            sapaan.isNotEmpty ? sapaan[0].toUpperCase() : 'U',
                            style: const TextStyle(
                              fontSize: 26,
                              fontWeight: FontWeight.w700,
                              color: Color(0xFF0051D5),
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              isRT ? (namaLengkap.startsWith('Pak') ? namaLengkap : 'Pak $sapaan') : namaLengkap,
                              style: const TextStyle(
                                fontSize: 18.0,
                                fontWeight: FontWeight.w700,
                                color: Color(0xFF00152A),
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                            const SizedBox(height: 4),
                            Row(
                              children: [
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 2.0),
                                  decoration: BoxDecoration(
                                    color: const Color(0xFFDBE1FF).withValues(alpha: 0.5),
                                    borderRadius: BorderRadius.circular(9999.0),
                                  ),
                                  child: Text(
                                    isRT ? 'Ketua RT' : 'Warga',
                                    style: const TextStyle(
                                      fontSize: 11.0,
                                      fontWeight: FontWeight.w700,
                                      color: Color(0xFF0051D5),
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 6),
                                const Icon(
                                  Icons.verified_rounded,
                                  size: 14,
                                  color: Color(0xFF0051D5),
                                ),
                                const SizedBox(width: 3),
                                const Text(
                                  'Terverifikasi',
                                  style: TextStyle(
                                    fontSize: 11.0,
                                    fontWeight: FontWeight.w500,
                                    color: Color(0xFF64748B),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 4),
                            const Text(
                              'RT 04 / RW 09, Gunungsari Indah',
                              style: TextStyle(
                                fontSize: 11.0,
                                fontWeight: FontWeight.w400,
                                color: Color(0xFF64748B),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),
                  // Tombol Ubah Profil
                  InkWell(
                    onTap: () => context.push(RouteNames.editProfile),
                    borderRadius: BorderRadius.circular(12.0),
                    child: Container(
                      width: double.infinity,
                      height: 42,
                      decoration: BoxDecoration(
                        color: const Color(0xFFF5F6FF),
                        borderRadius: BorderRadius.circular(12.0),
                      ),
                      child: const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.edit_note_rounded,
                            size: 18,
                            color: Color(0xFF0051D5),
                          ),
                          SizedBox(width: 6),
                          Text(
                            'Ubah Profil',
                            style: TextStyle(
                              fontSize: 13.0,
                              fontWeight: FontWeight.w700,
                              color: Color(0xFF0051D5),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 24),

            // 2. Data Pribadi Section
            const Text(
              'Data Pribadi',
              style: TextStyle(
                fontSize: 18.0,
                fontWeight: FontWeight.w700,
                color: Color(0xFF00152A),
              ),
            ),
            const SizedBox(height: 12),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16.0),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0x06000000),
                    blurRadius: 10,
                    offset: Offset(0, 2),
                  ),
                ],
              ),
              child: Column(
                children: [
                  _buildDataRow(
                    icon: Icons.person_outline_rounded,
                    label: 'Nama lengkap',
                    value: namaLengkap,
                  ),
                  const Divider(color: Color(0xFFECEEF0), height: 1),
                  _buildDataRow(
                    icon: Icons.badge_outlined,
                    label: 'NIK',
                    value: nik,
                  ),
                  const Divider(color: Color(0xFFECEEF0), height: 1),
                  _buildDataRow(
                    icon: Icons.phone_outlined,
                    label: 'Nomor WhatsApp / Telepon',
                    value: noTelp,
                  ),
                  const Divider(color: Color(0xFFECEEF0), height: 1),
                  _buildDataRow(
                    icon: Icons.mail_outline_rounded,
                    label: 'Alamat email',
                    value: email,
                  ),
                  const Divider(color: Color(0xFFECEEF0), height: 1),
                  _buildDataRow(
                    icon: Icons.location_on_outlined,
                    label: 'Alamat lengkap',
                    value: alamat,
                    isMultiLine: true,
                  ),
                ],
              ),
            ),

            const SizedBox(height: 24),

            // 3. Akun & Bantuan Section
            const Text(
              'Akun & Bantuan',
              style: TextStyle(
                fontSize: 18.0,
                fontWeight: FontWeight.w700,
                color: Color(0xFF00152A),
              ),
            ),
            const SizedBox(height: 12),
            Container(
              width: double.infinity,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16.0),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0x06000000),
                    blurRadius: 10,
                    offset: Offset(0, 2),
                  ),
                ],
              ),
              child: Column(
                children: [
                  _buildActionMenuTile(
                    icon: Icons.draw_outlined,
                    title: 'Tanda Tangan',
                    onTap: () => context.push(RouteNames.signature),
                  ),
                  const Divider(color: Color(0xFFECEEF0), height: 1, indent: 56),
                  _buildActionMenuTile(
                    icon: Icons.notifications_none_rounded,
                    title: 'Notifikasi',
                    onTap: () => context.push(RouteNames.notifications),
                  ),
                  const Divider(color: Color(0xFFECEEF0), height: 1, indent: 56),
                  _buildActionMenuTile(
                    icon: Icons.shield_outlined,
                    title: 'Pengaturan Akun',
                    onTap: () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Pengaturan akun segera hadir.')),
                      );
                    },
                  ),
                  const Divider(color: Color(0xFFECEEF0), height: 1, indent: 56),
                  _buildActionMenuTile(
                    icon: Icons.help_outline_rounded,
                    title: 'Pusat Bantuan',
                    onTap: () => context.go(RouteNames.chatbot),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // 4. Tombol Keluar Akun
            InkWell(
              onTap: () => _showLogoutDialog(context, ref),
              borderRadius: BorderRadius.circular(12.0),
              child: Container(
                width: double.infinity,
                height: 46,
                decoration: BoxDecoration(
                  color: const Color(0xFFFFF4F3),
                  borderRadius: BorderRadius.circular(12.0),
                ),
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      Icons.logout_rounded,
                      size: 18,
                      color: Color(0xFFBA1A1A),
                    ),
                    SizedBox(width: 8),
                    Text(
                      'Keluar Akun',
                      style: TextStyle(
                        fontSize: 13.0,
                        fontWeight: FontWeight.w700,
                        color: Color(0xFFBA1A1A),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildDataRow({
    required IconData icon,
    required String label,
    required String value,
    bool isMultiLine = false,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12.0),
      child: Row(
        crossAxisAlignment: isMultiLine ? CrossAxisAlignment.start : CrossAxisAlignment.center,
        children: [
          Icon(icon, size: 20, color: const Color(0xFF64748B)),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: const TextStyle(
                    fontSize: 11.0,
                    fontWeight: FontWeight.w400,
                    color: Color(0xFF64748B),
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  value,
                  style: const TextStyle(
                    fontSize: 13.0,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF00152A),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActionMenuTile({
    required IconData icon,
    required String title,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16.0),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
        child: Row(
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: const Color(0xFFF7F9FB),
                borderRadius: BorderRadius.circular(10.0),
              ),
              child: Icon(icon, size: 18, color: const Color(0xFF64748B)),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                title,
                style: const TextStyle(
                  fontSize: 13.0,
                  fontWeight: FontWeight.w600,
                  color: Color(0xFF00152A),
                ),
              ),
            ),
            const Icon(
              Icons.chevron_right_rounded,
              size: 20,
              color: Color(0xFF94A3B8),
            ),
          ],
        ),
      ),
    );
  }

  void _showLogoutDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Konfirmasi Keluar'),
        content: const Text('Apakah Anda yakin ingin keluar dari akun RTConnect?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Batal'),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(ctx);
              await ref.read(authControllerProvider.notifier).logout();
              if (context.mounted) {
                context.go(RouteNames.login);
              }
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFBA1A1A),
            ),
            child: const Text('Keluar', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }
}
