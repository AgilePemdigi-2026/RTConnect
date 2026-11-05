import 'dart:typed_data';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/router/route_names.dart';
import '../../../core/theme/app_typography.dart';
import '../../auth/presentation/auth_controller.dart';
import 'profile_controller.dart';

/// Screen: Tanda Tangan Page (Grounded in Figma Node #191:1136)
class SignatureScreen extends ConsumerStatefulWidget {
  const SignatureScreen({super.key});

  @override
  ConsumerState<SignatureScreen> createState() => _SignatureScreenState();
}

class _SignatureScreenState extends ConsumerState<SignatureScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(profileControllerProvider.notifier).loadSignature();
    });
  }

  String _formatUploadDate(DateTime? updatedAt, bool hasSignature) {
    if (updatedAt != null) {
      const months = [
        '',
        'Januari',
        'Februari',
        'Maret',
        'April',
        'Mei',
        'Juni',
        'Juli',
        'Agustus',
        'September',
        'Oktober',
        'November',
        'Desember'
      ];
      return '${updatedAt.day} ${months[updatedAt.month]} ${updatedAt.year}';
    }
    return hasSignature ? 'Aktif terverifikasi' : 'Belum diunggah';
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authControllerProvider);
    final profileState = ref.watch(profileControllerProvider);
    final user = authState.user;
    final signatureUrl = user?.signatureUrl;
    final hasSignature =
        (signatureUrl != null && signatureUrl.isNotEmpty) ||
        (profileState.signatureBytes != null && profileState.signatureBytes!.isNotEmpty);

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
                    onTap: () => Navigator.canPop(context)
                        ? Navigator.pop(context)
                        : context.go(RouteNames.profile),
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
                    'Tanda Tangan',
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
            // 1. Tanda Tangan Saat Ini
            const Text(
              'Tanda tangan saat ini',
              style: TextStyle(
                fontSize: 18.0,
                fontWeight: FontWeight.w700,
                color: Color(0xFF00152A),
              ),
            ),
            const SizedBox(height: 12),

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
                  // Pratinjau Tanda Tangan
                  Container(
                    width: double.infinity,
                    height: 184,
                    decoration: BoxDecoration(
                      color: const Color(0xFFFAFCFF),
                      borderRadius: BorderRadius.circular(10.0),
                      border: Border.all(color: const Color(0xFFECEEF0)),
                    ),
                    child: _buildSignatureContent(profileState, hasSignature),
                  ),
                  const SizedBox(height: 16),

                  // Tanggal Unggah
                  Row(
                    children: [
                      const Icon(
                        Icons.calendar_today_outlined,
                        size: 18,
                        color: Color(0xFF64748B),
                      ),
                      const SizedBox(width: 10),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Tanggal diunggah',
                            style: TextStyle(
                              fontSize: 11.0,
                              fontWeight: FontWeight.w400,
                              color: Color(0xFF64748B),
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            _formatUploadDate(
                              profileState.signatureUpdatedAt,
                              hasSignature,
                            ),
                            style: const TextStyle(
                              fontSize: 13.0,
                              fontWeight: FontWeight.w600,
                              color: Color(0xFF00152A),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            // 2. Ketentuan Tanda Tangan Card
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16.0),
              decoration: BoxDecoration(
                color: const Color(0xFFF0F4FF),
                borderRadius: BorderRadius.circular(12.0),
                border: Border.all(color: const Color(0xFFDBE1FF)),
              ),
              child: const Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(
                    Icons.info_outline_rounded,
                    size: 20,
                    color: Color(0xFF0051D5),
                  ),
                  SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Satu tanda tangan saja',
                          style: TextStyle(
                            fontSize: 13.0,
                            fontWeight: FontWeight.w700,
                            color: Color(0xFF00152A),
                          ),
                        ),
                        SizedBox(height: 4),
                        Text(
                          'Mengunggah tanda tangan baru akan menggantikan tanda tangan saat ini, bukan menambah tanda tangan lain.',
                          style: TextStyle(
                            fontSize: 12.0,
                            fontWeight: FontWeight.w400,
                            color: Color(0xFF64748B),
                            height: 1.4,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 28),

            // 3. Tombol Perbarui Tanda Tangan
            SizedBox(
              width: double.infinity,
              height: 48,
              child: ElevatedButton.icon(
                onPressed: () => _openSignaturePad(context),
                icon: const Icon(Icons.draw_rounded, size: 18, color: Colors.white),
                label: const Text(
                  'Perbarui Tanda Tangan',
                  style: TextStyle(
                    fontSize: 13.0,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                  ),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF0051D5),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12.0),
                  ),
                  elevation: 0,
                ),
              ),
            ),

            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  Widget _buildSignatureContent(ProfileState profileState, bool hasSignature) {
    if (profileState.isSignatureLoading) {
      return const Center(
        child: SizedBox(
          width: 30,
          height: 30,
          child: CircularProgressIndicator(
            strokeWidth: 2.5,
            color: Color(0xFF0051D5),
          ),
        ),
      );
    }

    if (profileState.signatureBytes != null && profileState.signatureBytes!.isNotEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Image.memory(
            profileState.signatureBytes!,
            fit: BoxFit.contain,
          ),
        ),
      );
    }

    if (hasSignature) {
      return Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: const Color(0xFF0051D5).withValues(alpha: 0.08),
            ),
            child: const Icon(
              Icons.check_circle_outline_rounded,
              size: 26,
              color: Color(0xFF0051D5),
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Tanda tangan digital tersimpan',
            style: TextStyle(
              fontSize: 12.0,
              fontWeight: FontWeight.w600,
              color: Color(0xFF00152A),
            ),
          ),
        ],
      );
    }

    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Container(
          width: 56,
          height: 56,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: const Color(0xFF0051D5).withValues(alpha: 0.08),
          ),
          child: const Icon(
            Icons.draw_outlined,
            size: 28,
            color: Color(0xFF0051D5),
          ),
        ),
        const SizedBox(height: 10),
        const Text(
          'Belum ada tanda tangan digital',
          style: TextStyle(
            fontSize: 12.0,
            fontWeight: FontWeight.w400,
            color: Color(0xFF64748B),
          ),
        ),
      ],
    );
  }

  void _openSignaturePad(BuildContext context) {
    final messenger = ScaffoldMessenger.of(context);
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => _SignaturePadBottomSheet(
        onSignatureSaved: (bytes) async {
          Navigator.pop(ctx);
          final success = await ref
              .read(profileControllerProvider.notifier)
              .updateSignature(
                fileBytes: bytes,
                fileName: 'signature_${DateTime.now().millisecondsSinceEpoch}.png',
              );
          if (success) {
            messenger.showSnackBar(
              const SnackBar(
                content: Text('Tanda tangan digital berhasil disimpan'),
                backgroundColor: Color(0xFF0051D5),
              ),
            );
          } else {
            final error = ref.read(profileControllerProvider).errorMessage;
            messenger.showSnackBar(
              SnackBar(
                content: Text(error ?? 'Gagal menyimpan tanda tangan'),
                backgroundColor: const Color(0xFFBA1A1A),
              ),
            );
          }
        },
      ),
    );
  }
}

class _SignaturePadBottomSheet extends StatefulWidget {
  final ValueChanged<Uint8List> onSignatureSaved;

  const _SignaturePadBottomSheet({required this.onSignatureSaved});

  @override
  State<_SignaturePadBottomSheet> createState() => _SignaturePadBottomSheetState();
}

class _SignaturePadBottomSheetState extends State<_SignaturePadBottomSheet> {
  final List<Offset?> _points = [];
  bool _isSaving = false;

  Future<Uint8List?> _captureSignature() async {
    final validPoints = _points.whereType<Offset>().toList();
    if (validPoints.isEmpty) return null;

    // Find bounding box
    double minX = validPoints.first.dx;
    double maxX = validPoints.first.dx;
    double minY = validPoints.first.dy;
    double maxY = validPoints.first.dy;

    for (final p in validPoints) {
      if (p.dx < minX) minX = p.dx;
      if (p.dx > maxX) maxX = p.dx;
      if (p.dy < minY) minY = p.dy;
      if (p.dy > maxY) maxY = p.dy;
    }

    const double padding = 24.0;
    const double targetWidth = 400.0;
    const double targetHeight = 200.0;

    final double rawWidth = (maxX - minX).clamp(10.0, double.infinity);
    final double rawHeight = (maxY - minY).clamp(10.0, double.infinity);

    const double availableWidth = targetWidth - (padding * 2);
    const double availableHeight = targetHeight - (padding * 2);

    final double scaleX = availableWidth / rawWidth;
    final double scaleY = availableHeight / rawHeight;
    final double scale = (scaleX < scaleY ? scaleX : scaleY).clamp(0.01, 1.5);

    final double scaledWidth = rawWidth * scale;
    final double scaledHeight = rawHeight * scale;

    final double offsetX = (targetWidth - scaledWidth) / 2 - (minX * scale);
    final double offsetY = (targetHeight - scaledHeight) / 2 - (minY * scale);

    final recorder = ui.PictureRecorder();
    final canvas = Canvas(recorder, const Rect.fromLTWH(0, 0, targetWidth, targetHeight));

    // Transparent / clean white background
    final bgPaint = Paint()..color = Colors.white;
    canvas.drawRect(const Rect.fromLTWH(0, 0, targetWidth, targetHeight), bgPaint);

    final linePaint = Paint()
      ..color = const Color(0xFF00152A)
      ..strokeCap = StrokeCap.round
      ..strokeWidth = 3.5;

    for (int i = 0; i < _points.length - 1; i++) {
      if (_points[i] != null && _points[i + 1] != null) {
        final p1 = Offset(
          _points[i]!.dx * scale + offsetX,
          _points[i]!.dy * scale + offsetY,
        );
        final p2 = Offset(
          _points[i + 1]!.dx * scale + offsetX,
          _points[i + 1]!.dy * scale + offsetY,
        );
        canvas.drawLine(p1, p2, linePaint);
      }
    }

    final picture = recorder.endRecording();
    final img = await picture.toImage(targetWidth.toInt(), targetHeight.toInt());
    final byteData = await img.toByteData(format: ui.ImageByteFormat.png);
    return byteData?.buffer.asUint8List();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20.0),
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24.0)),
      ),
      child: SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Buat Tanda Tangan Digital',
                  style: TextStyle(
                    fontSize: 16.0,
                    fontWeight: FontWeight.w700,
                    color: Color(0xFF00152A),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close_rounded),
                  onPressed: () => Navigator.pop(context),
                ),
              ],
            ),
            const SizedBox(height: 8),
            const Text(
              'Goreskan tanda tangan Anda pada area kanvas di bawah.',
              style: TextStyle(fontSize: 12.0, color: Color(0xFF64748B)),
            ),
            const SizedBox(height: 12),
            Container(
              height: 200,
              width: double.infinity,
              decoration: BoxDecoration(
                color: const Color(0xFFFAFCFF),
                borderRadius: BorderRadius.circular(12.0),
                border: Border.all(color: const Color(0xFF0051D5).withValues(alpha: 0.3)),
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(12.0),
                child: GestureDetector(
                  onPanUpdate: (details) {
                    setState(() {
                      _points.add(details.localPosition);
                    });
                  },
                  onPanEnd: (_) => setState(() => _points.add(null)),
                  child: CustomPaint(
                    painter: _DrawingPainter(_points),
                    size: Size.infinite,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: _isSaving ? null : () => setState(() => _points.clear()),
                    style: OutlinedButton.styleFrom(
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10.0),
                      ),
                      padding: const EdgeInsets.symmetric(vertical: 12.0),
                    ),
                    child: const Text('Bersihkan'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton(
                    onPressed: _isSaving
                        ? null
                        : () async {
                            setState(() => _isSaving = true);
                            try {
                              final bytes = await _captureSignature();
                              if (bytes != null) {
                                widget.onSignatureSaved(bytes);
                              } else {
                                if (context.mounted) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(
                                      content: Text('Kanvas tanda tangan masih kosong'),
                                    ),
                                  );
                                }
                              }
                            } finally {
                              if (mounted) setState(() => _isSaving = false);
                            }
                          },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF0051D5),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10.0),
                      ),
                      padding: const EdgeInsets.symmetric(vertical: 12.0),
                    ),
                    child: _isSaving
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Text('Simpan', style: TextStyle(color: Colors.white)),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
          ],
        ),
      ),
    );
  }
}

class _DrawingPainter extends CustomPainter {
  final List<Offset?> points;

  _DrawingPainter(this.points);

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0xFF00152A)
      ..strokeCap = StrokeCap.round
      ..strokeWidth = 3.0;

    for (int i = 0; i < points.length - 1; i++) {
      if (points[i] != null && points[i + 1] != null) {
        canvas.drawLine(points[i]!, points[i + 1]!, paint);
      }
    }
  }

  @override
  bool shouldRepaint(covariant _DrawingPainter oldDelegate) => true;
}
