/// REST API Endpoints mapping to api.md specifications
class ApiEndpoints {
  // Auth
  static const String register = '/auth/register'; // API-001
  static const String login = '/auth/login'; // API-002
  static const String me = '/auth/me'; // API-003

  // Letters
  static const String letterTypes = '/letters/types'; // API-004
  static const String applyLetter = '/letters/apply'; // API-005
  static const String myApplications = '/letters/my-applications'; // API-006
  static const String incomingQueue = '/letters/incoming-queue'; // API-007
  static String letterDetail(int id) => '/letters/$id'; // API-008
  static String resubmitLetter(int id) => '/letters/$id/resubmit'; // API-009
  static String letterDecision(int id) => '/letters/$id/decision'; // API-010
  static String signDigital(int id) => '/letters/$id/sign-digital'; // API-011 (Image Overlay)
  static String confirmPhysical(int id) => '/letters/$id/confirm-physical'; // API-012
  static String downloadLetter(int id) => '/letters/$id/download'; // API-013

  // Chatbot & Notifications
  static const String chatbotQuery = '/chatbot/query'; // API-014
  static const String notifications = '/notifications'; // API-015
}
