import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:syncfusion_flutter_pdfviewer/pdfviewer.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/errors/app_exception.dart';
import '../../../core/network/api_client.dart';
import '../../../core/network/api_endpoints.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_typography.dart';

class PdfViewerScreen extends ConsumerStatefulWidget {
  final int applicationId;

  const PdfViewerScreen({super.key, required this.applicationId});

  @override
  ConsumerState<PdfViewerScreen> createState() => _PdfViewerScreenState();
}

class _PdfViewerScreenState extends ConsumerState<PdfViewerScreen> {
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  String? _token;
  bool _isLoading = true;
  bool _isDownloading = false;

  @override
  void initState() {
    super.initState();
    _loadToken();
  }

  Future<void> _loadToken() async {
    final token = await _storage.read(key: AppConstants.keyAuthToken);
    setState(() {
      _token = token;
      _isLoading = false;
    });
  }

  void _showMessage(String message, Color color) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(backgroundColor: color, content: Text(message)));
  }

  /// Meminta tautan unduhan berumur pendek ke backend, lalu membukanya di
  /// browser / pengelola unduhan HP. File disimpan ke folder Unduhan oleh
  /// sistem, jadi tidak butuh izin penyimpanan.
  Future<void> _downloadPdf() async {
    if (_isDownloading) return;
    setState(() => _isDownloading = true);
    try {
      final response = await ApiClient().dio.get<Map<String, dynamic>>(
        ApiEndpoints.downloadLetterLink(widget.applicationId),
      );
      final data = response.data?['data'];
      final path = data is Map ? data['download_path']?.toString() : null;
      if (path == null || path.isEmpty) {
        throw Exception('Tautan unduhan tidak tersedia');
      }
      final base = response.requestOptions.baseUrl.replaceFirst(
        RegExp(r'/+$'),
        '',
      );
      final opened = await launchUrl(
        Uri.parse('$base$path'),
        mode: LaunchMode.externalApplication,
        webOnlyWindowName: '_self',
      );
      if (!opened) throw Exception('Tidak dapat membuka tautan unduhan');
      _showMessage(
        'Unduhan dimulai. Periksa folder Unduhan atau notifikasi unduhan di HP Anda.',
        AppColors.success,
      );
    } catch (e) {
      final message = (e is DioException && e.error is AppException)
          ? (e.error as AppException).message
          : e.toString().replaceFirst('Exception: ', '');
      _showMessage(message, AppColors.error);
    } finally {
      if (mounted) setState(() => _isDownloading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    final downloadUrl =
        '${AppConstants.defaultBaseUrl}${ApiEndpoints.downloadLetter(widget.applicationId)}';

    return Scaffold(
      backgroundColor: AppColors.surface,
      appBar: AppBar(
        title: Text('Surat RTConnect (PDF)', style: AppTypography.heading3),
        centerTitle: true,
        backgroundColor: AppColors.surface,
        elevation: 0,
        actions: [
          IconButton(
            icon: _isDownloading
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.download, color: AppColors.primary),
            tooltip: 'Unduh Berkas',
            onPressed: _isDownloading ? null : _downloadPdf,
          ),
        ],
      ),
      body: SafeArea(
        child: _token != null
            ? SfPdfViewer.network(
                downloadUrl,
                headers: {'Authorization': 'Bearer $_token'},
                canShowScrollHead: true,
                canShowScrollStatus: true,
                onDocumentLoadFailed: (details) {
                  _showMessage(
                    'Gagal memuat PDF: ${details.description}',
                    AppColors.error,
                  );
                },
              )
            : const Center(
                child: Text('Autentikasi diperlukan untuk melihat berkas ini'),
              ),
      ),
    );
  }
}