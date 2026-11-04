import 'dart:typed_data';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/constants/app_constants.dart';
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
  Widget build(BuildContext context) {
    final authState = ref.watch(authControllerProvider);
    final user = authState.user;
    final signatureUrl = user?.signatureUrl;
    final hasSignature = signatureUrl != null && signatureUrl.isNotEmpty;

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
                    onTap: () => Navigator.canPop(context) ? Navigator.pop(context) : context.go(RouteNames.profile),
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
                    child: hasSignature
                        ? Center(
                            child: Padding(
                              padding: const EdgeInsets.all(16.0),
                              child: _buildSignatureImage(signatureUrl),
                            ),
                          )
                        : Column(
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
                                'Ilustrasi tanda tangan',
                                style: TextStyle(
                                  fontSize: 11.0,
                                  fontWeight: FontWeight.w400,
                                  color: Color(0xFF64748B),
                                ),
                              ),
                            ],
                          ),
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
                            hasSignature ? '12 Oktober 2026' : 'Belum diunggah',
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

  Widget _buildSignatureImage(String path) {
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return Image.network(
        path,
        fit: BoxFit.contain,
        errorBuilder: (ctx, err, stack) => _buildSignatureFallback(),
      );
    }
    final fullUrl = '${AppConstants.defaultBaseUrl.replaceFirst(RegExp(r'/api/v1/?$'), '')}/uploads/$path';
    return Image.network(
      fullUrl,
      fit: BoxFit.contain,
      errorBuilder: (ctx, err, stack) => _buildSignatureFallback(),
    );
  }

  Widget _buildSignatureFallback() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        CustomPaint(
          size: const Size(220, 80),
          painter: _SampleSignaturePainter(),
        ),
        const SizedBox(height: 8),
        const Text(
          'Tanda tangan digital aktif',
          style: TextStyle(fontSize: 11.0, color: Color(0xFF64748B)),
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
          final success = await ref.read(profileControllerProvider.notifier).updateSignature(
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

class _SampleSignaturePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0xFF00152A)
      ..strokeWidth = 2.5
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    final path = Path();
    path.moveTo(size.width * 0.15, size.height * 0.7);
    path.quadraticBezierTo(size.width * 0.3, size.height * 0.1, size.width * 0.45, size.height * 0.6);
    path.quadraticBezierTo(size.width * 0.6, size.height * 0.9, size.width * 0.75, size.height * 0.3);
    path.lineTo(size.width * 0.85, size.height * 0.4);

    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _SignaturePadBottomSheet extends StatefulWidget {
  final ValueChanged<Uint8List> onSignatureSaved;

  const _SignaturePadBottomSheet({required this.onSignatureSaved});

  @override
  State<_SignaturePadBottomSheet> createState() => _SignaturePadBottomSheetState();
}

class _SignaturePadBottomSheetState extends State<_SignaturePadBottomSheet> {
  final List<Offset?> _points = [];

  Future<Uint8List?> _captureSignature() async {
    if (_points.isEmpty) return null;
    final recorder = ui.PictureRecorder();
    final canvas = Canvas(recorder, const Rect.fromLTWH(0, 0, 400, 200));

    final bgPaint = Paint()..color = Colors.white;
    canvas.drawRect(const Rect.fromLTWH(0, 0, 400, 200), bgPaint);

    final linePaint = Paint()
      ..color = const Color(0xFF00152A)
      ..strokeCap = StrokeCap.round
      ..strokeWidth = 3.0;

    for (int i = 0; i < _points.length - 1; i++) {
      if (_points[i] != null && _points[i + 1] != null) {
        canvas.drawLine(_points[i]!, _points[i + 1]!, linePaint);
      }
    }

    final picture = recorder.endRecording();
    final img = await picture.toImage(400, 200);
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
                      final box = context.findRenderObject() as RenderBox?;
                      if (box != null) {
                        _points.add(details.localPosition);
                      }
                    });
                  },
                  onPanEnd: (details) => _points.add(null),
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
                    onPressed: () => setState(() => _points.clear()),
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
                    onPressed: () async {
                      final bytes = await _captureSignature();
                      if (bytes != null) {
                        widget.onSignatureSaved(bytes);
                      } else {
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('Kanvas tanda tangan masih kosong')),
                          );
                        }
                      }
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF0051D5),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10.0),
                      ),
                      padding: const EdgeInsets.symmetric(vertical: 12.0),
                    ),
                    child: const Text('Simpan', style: TextStyle(color: Colors.white)),
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
