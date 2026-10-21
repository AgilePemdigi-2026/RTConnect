/// Route constants for RTConnect GoRouter
class RouteNames {
  static const String landing = '/';
  static const String login = '/login';
  static const String register = '/register';

  // Warga Routes
  static const String wargaHome = '/warga/home';
  static const String wargaPengajuan = '/warga/pengajuan';
  static const String wargaPengajuanBaru = '/warga/pengajuan/baru';
  static const String wargaPengajuanRevisi = '/warga/pengajuan/revisi/:id';
  static const String chatbot = '/chatbot';

  // RT Head Routes
  static const String rtHome = '/rt/home';
  static const String rtQueue = '/rt/pengajuan';
  static const String rtDetail = '/rt/pengajuan/:id';

  // Shared Preview & Notifications
  static const String pdfPreview = '/surat/preview/:id';
  static const String notifications = '/notifications';
}
