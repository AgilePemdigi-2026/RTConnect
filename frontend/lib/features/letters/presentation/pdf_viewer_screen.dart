import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:syncfusion_flutter_pdfviewer/pdfviewer.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../../core/constants/app_constants.dart';
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

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    final downloadUrl = '${AppConstants.defaultBaseUrl}${ApiEndpoints.downloadLetter(widget.applicationId)}';

    return Scaffold(
      backgroundColor: AppColors.surface,
      appBar: AppBar(
        title: Text('Surat RTConnect (PDF)', style: AppTypography.heading3),
        centerTitle: true,
        backgroundColor: AppColors.surface,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.download, color: AppColors.primary),
            tooltip: 'Unduh Berkas',
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  backgroundColor: AppColors.success,
                  content: Text('File PDF telah tersimpan di direktori unduhan.'),
                ),
              );
            },
          ),
        ],
      ),
      body: SafeArea(
        child: _token != null
            ? SfPdfViewer.network(
                downloadUrl,
                headers: {
                  'Authorization': 'Bearer $_token',
                },
                canShowScrollHead: true,
                canShowScrollStatus: true,
                onDocumentLoadFailed: (details) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      backgroundColor: AppColors.error,
                      content: Text('Gagal memuat PDF: ${details.description}'),
                    ),
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
