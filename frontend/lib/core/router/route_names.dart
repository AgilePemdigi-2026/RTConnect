/// Route constants for RTConnect GoRouter
class RouteNames {
  static const String landing = '/';
  static const String login = '/login';
  static const String register = '/register';

  // Warga Routes
  static const String wargaHome = '/warga/home';
  static const String wargaPengajuan = '/warga/pengajuan';
  static const String wargaPengajuanBaru = '/warga/pengajuan/baru'; // Asisten AI (layar awal pengajuan)
  static const String wargaPengajuanManual = '/warga/pengajuan/manual'; // formulir manual
  static const String wargaPengajuanRevisi = '/warga/pengajuan/revisi/:id';
  static const String chatbot = '/chatbot';

  // RT Head Routes
  static const String rtHome = '/rt/home';
  static const String rtQueue = '/rt/pengajuan';
  static const String rtDetail = '/rt/pengajuan/:id';

  // Shared Profile & Signature Routes
  static const String profile = '/profile';
  static const String editProfile = '/profile/edit';
  static const String signature = '/profile/signature';

  // Shared Preview & Notifications
  static const String pdfPreview = '/surat/preview/:id';
  static const String notifications = '/notifications';
}
