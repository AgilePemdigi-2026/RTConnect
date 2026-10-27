import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../rt_theme.dart';
import '../services/pengajuan_rt_service.dart';

/// Popup "Otorisasi Keamanan" (Gambar 1.8).
/// Mengembalikan [AksiResult] kalau pengesahan berhasil, atau null kalau dibatalkan.
Future<AksiResult?> showPinKeamananDialog(
  BuildContext context, {
  required Future<AksiResult> Function(String pin) onSubmit,
}) {
  return showDialog<AksiResult>(
    context: context,
    barrierDismissible: false,
    builder: (_) => _PinKeamananDialog(onSubmit: onSubmit),
  );
}

class _PinKeamananDialog extends StatefulWidget {
  final Future<AksiResult> Function(String pin) onSubmit;
  const _PinKeamananDialog({required this.onSubmit});

  @override
  State<_PinKeamananDialog> createState() => _PinKeamananDialogState();
}

class _PinKeamananDialogState extends State<_PinKeamananDialog> {
  static const _panjang = 6;
  final _ctrl = TextEditingController();
  final _focus = FocusNode();
  bool _tampilkan = false;
  bool _loading = false;
  bool _terkunci = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _ctrl.addListener(() => setState(() {}));
    WidgetsBinding.instance.addPostFrameCallback((_) => _focus.requestFocus());
  }

  @override
  void dispose() {
    _ctrl.dispose();
    _focus.dispose();
    super.dispose();
  }

  bool get _lengkap => _ctrl.text.length == _panjang;

  Future<void> _konfirmasi() async {
    if (!_lengkap || _loading || _terkunci) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    final hasil = await widget.onSubmit(_ctrl.text);
    if (!mounted) return;
    if (hasil.sukses) {
      Navigator.of(context).pop(hasil);
      return;
    }
    setState(() {
      _loading = false;
      _terkunci = hasil.terkunci;
      _error = hasil.sisaPercobaan != null
          ? '${hasil.pesan}. Sisa percobaan: ${hasil.sisaPercobaan}'
          : hasil.pesan;
      _ctrl.clear();
    });
    if (!_terkunci) _focus.requestFocus();
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      insetPadding: const EdgeInsets.symmetric(horizontal: 20),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Header
            Row(children: [
              const Icon(Icons.lock_outline, size: 16, color: RtColors.navy),
              const SizedBox(width: 6),
              const Expanded(
                child: Text('OTORISASI KEAMANAN',
                    style: TextStyle(
                        fontSize: 12, fontWeight: FontWeight.w600, letterSpacing: 0.4)),
              ),
              IconButton(
                visualDensity: VisualDensity.compact,
                style: IconButton.styleFrom(backgroundColor: RtColors.field),
                icon: const Icon(Icons.close, size: 18),
                onPressed: _loading ? null : () => Navigator.of(context).pop(),
              ),
            ]),
            const Divider(height: 20),
            const CircleAvatar(
              radius: 24,
              backgroundColor: RtColors.navy,
              child: Icon(Icons.shield_outlined, color: Colors.white),
            ),
            const SizedBox(height: 14),
            const Text('Konfirmasi Persetujuan',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            const SizedBox(height: 6),
            const Text(
              'Masukkan PIN keamanan 6 digit untuk mengonfirmasi persetujuan dan pengesahan surat ini.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 13, color: RtColors.muted),
            ),
            const SizedBox(height: 18),
            Row(children: [
              const Expanded(
                child: Text('PIN Keamanan RT (6 Digit)',
                    style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
              ),
              TextButton.icon(
                style: TextButton.styleFrom(
                    padding: EdgeInsets.zero, visualDensity: VisualDensity.compact),
                onPressed: () => setState(() => _tampilkan = !_tampilkan),
                icon: Icon(_tampilkan ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                    size: 16),
                label: Text(_tampilkan ? 'Sembunyikan' : 'Tampilkan PIN',
                    style: const TextStyle(fontSize: 12)),
              ),
            ]),
            const SizedBox(height: 6),
            _kotakPin(),
            if (_error != null) ...[
              const SizedBox(height: 10),
              Row(children: [
                const Icon(Icons.error_outline, size: 16, color: RtColors.danger),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(_error!,
                      style: const TextStyle(color: RtColors.danger, fontSize: 12.5)),
                ),
              ]),
            ],
            const SizedBox(height: 18),
            SizedBox(
              width: double.infinity,
              height: 48,
              child: FilledButton.icon(
                style: FilledButton.styleFrom(
                  backgroundColor: RtColors.success,
                  disabledBackgroundColor: RtColors.success.withValues(alpha: 0.45),
                  disabledForegroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                onPressed: _lengkap && !_loading && !_terkunci ? _konfirmasi : null,
                icon: _loading
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : const Icon(Icons.check_circle_outline, size: 20),
                label: Text(_terkunci ? 'PIN Terkunci' : 'Konfirmasi & Setujui'),
              ),
            ),
            const SizedBox(height: 8),
            SizedBox(
              width: double.infinity,
              height: 44,
              child: TextButton(
                style: TextButton.styleFrom(
                  backgroundColor: RtColors.field,
                  foregroundColor: RtColors.navy,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                onPressed: _loading ? null : () => Navigator.of(context).pop(),
                child: const Text('Batal'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// 6 kotak terpisah, input sebenarnya pakai 1 TextField tersembunyi.
  Widget _kotakPin() {
    final teks = _ctrl.text;
    return GestureDetector(
      onTap: () => _focus.requestFocus(),
      child: Stack(children: [
        // TextField tak terlihat yang menerima input keyboard
        Opacity(
          opacity: 0,
          child: SizedBox(
            height: 52,
            child: TextField(
              controller: _ctrl,
              focusNode: _focus,
              enabled: !_terkunci && !_loading,
              keyboardType: TextInputType.number,
              maxLength: _panjang,
              autofillHints: const [],
              enableSuggestions: false,
              autocorrect: false,
              inputFormatters: [FilteringTextInputFormatter.digitsOnly],
              decoration: const InputDecoration(counterText: ''),
              onSubmitted: (_) => _konfirmasi(),
            ),
          ),
        ),
        IgnorePointer(
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: List.generate(_panjang, (i) {
              final terisi = i < teks.length;
              final aktif = _focus.hasFocus && i == teks.length && !_terkunci;
              return Container(
                width: 42,
                height: 52,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: _terkunci ? RtColors.field : Colors.white,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(
                    color: _error != null && !terisi
                        ? RtColors.danger.withValues(alpha: 0.5)
                        : aktif
                            ? RtColors.primary
                            : const Color(0xFFD9DCE3),
                    width: aktif ? 2 : 1,
                  ),
                ),
                child: terisi
                    ? Text(_tampilkan ? teks[i] : '•',
                        style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700))
                    : null,
              );
            }),
          ),
        ),
      ]),
    );
  }
}
