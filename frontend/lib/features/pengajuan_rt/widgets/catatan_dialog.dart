import 'package:flutter/material.dart';

import '../rt_theme.dart';

/// Bottom sheet untuk "Minta Revisi" / "Tolak Pengajuan".
/// Isian wajib diisi (SRS 4.2.3 REQ-4). Mengembalikan teks, atau null kalau batal.
Future<String?> showCatatanSheet(
  BuildContext context, {
  required String judul,
  required String label,
  required String hint,
  required String tombol,
  required Color warna,
  String? awal,
}) {
  return showModalBottomSheet<String>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.white,
    shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
    builder: (_) => _CatatanSheet(
        judul: judul, label: label, hint: hint, tombol: tombol, warna: warna, awal: awal),
  );
}

class _CatatanSheet extends StatefulWidget {
  final String judul, label, hint, tombol;
  final Color warna;
  final String? awal;
  const _CatatanSheet(
      {required this.judul,
      required this.label,
      required this.hint,
      required this.tombol,
      required this.warna,
      this.awal});

  @override
  State<_CatatanSheet> createState() => _CatatanSheetState();
}

class _CatatanSheetState extends State<_CatatanSheet> {
  late final _ctrl = TextEditingController(text: widget.awal);
  String? _error;

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  void _kirim() {
    final t = _ctrl.text.trim();
    if (t.isEmpty) {
      setState(() => _error = '${widget.label} wajib diisi');
      return;
    }
    Navigator.of(context).pop(t);
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.fromLTRB(
          20, 12, 20, MediaQuery.of(context).viewInsets.bottom + 20),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                    color: const Color(0xFFD9DCE3), borderRadius: BorderRadius.circular(2))),
          ),
          const SizedBox(height: 16),
          Text(widget.judul, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
          const SizedBox(height: 14),
          Text('${widget.label} *',
              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
          const SizedBox(height: 6),
          TextField(
            controller: _ctrl,
            autofocus: true,
            minLines: 3,
            maxLines: 5,
            maxLength: 255,
            onChanged: (_) {
              if (_error != null) setState(() => _error = null);
            },
            decoration: InputDecoration(
              hintText: widget.hint,
              errorText: _error,
              filled: true,
              fillColor: RtColors.field,
              border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
            ),
          ),
          const SizedBox(height: 8),
          SizedBox(
            width: double.infinity,
            height: 48,
            child: FilledButton(
              style: FilledButton.styleFrom(
                backgroundColor: widget.warna,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              onPressed: _kirim,
              child: Text(widget.tombol),
            ),
          ),
        ],
      ),
    );
  }
}
