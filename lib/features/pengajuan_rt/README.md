# Front End: Kelola & Detail Pengajuan (Ketua RT)

## Struktur
```
lib/
├── main_demo_rt.dart                       # demo pakai data dummy
└── features/pengajuan_rt/
    ├── rt_theme.dart                       # warna, chip status, format tanggal
    ├── models/pengajuan.dart
    ├── services/pengajuan_rt_service.dart  # Api (Flask) + Mock (dummy)
    ├── pages/
    │   ├── kelola_pengajuan_page.dart      # Gambar 1.6
    │   └── detail_pengajuan_page.dart      # Gambar 1.7
    └── widgets/
        ├── pin_keamanan_dialog.dart        # Gambar 1.8
        └── catatan_dialog.dart             # input catatan revisi / alasan tolak
```

## Cara menjalankan
1. Tambahkan dependency di `pubspec.yaml`:
   ```yaml
   dependencies:
     http: ^1.2.0
   ```
2. `flutter pub get`
3. `flutter run -t lib/main_demo_rt.dart`
4. PIN dummy: **482913** (salah 5x → terkunci 15 menit)

Butuh Flutter 3.24+ (memakai `PopScope.onPopInvokedWithResult`).

## Sambung ke backend
Di `main_demo_rt.dart`, ganti `MockPengajuanRtService()` dengan:
```dart
ApiPengajuanRtService(
  baseUrl: 'http://10.0.2.2:5000/api', // emulator Android → localhost laptop
  tokenProvider: () => tokenJwtYangTersimpan,
)
```

Endpoint yang dipakai:
| Aksi | Method & Path | Body |
|---|---|---|
| Daftar | `GET /rt/pengajuan` | |
| Detail | `GET /rt/pengajuan/<id>` | |
| Minta revisi | `POST /rt/pengajuan/<id>/revisi` | `catatan_revisi` |
| Tolak | `POST /rt/pengajuan/<id>/tolak` | `alasan_penolakan` |
| Setujui TTD basah | `POST /rt/pengajuan/<id>/setuju` | |
| Sahkan TTD digital | `POST /rt/pengajuan/<id>/sahkan-digital` | `pin` |

Format respons aksi: `{"status": "success"|"error", "message": "...", "nomor_surat"?, "sisa_percobaan"?, "sisa_menit"?}`
