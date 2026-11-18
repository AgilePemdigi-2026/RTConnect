import 'package:flutter_test/flutter_test.dart';
import 'package:rtconnect/features/chatbot/data/chatbot_repository.dart';
import 'package:rtconnect/features/chatbot/presentation/chatbot_controller.dart';

class MockChatbotRepository implements ChatbotRepository {
  Map<String, dynamic>? mockResponse;
  Exception? mockError;
  String? lastQuery;
  int? lastSessionId;

  @override
  Future<Map<String, dynamic>> sendQuery({
    required String query,
    int? sessionId,
  }) async {
    lastQuery = query;
    lastSessionId = sessionId;
    if (mockError != null) throw mockError!;
    return mockResponse ?? {
      'session_id': 10,
      'is_escalated': false,
      'answer': 'Syarat KTP hilang adalah fotokopi KK dan surat kehilangan.',
      'citation': 'KTP-el Hilang (RTC-014)',
      'similarity_score': 0.89,
      'status': 'SUMBER_DITEMUKAN',
      'escalation_whatsapp_url': null,
    };
  }

  @override
  Future<List<Map<String, dynamic>>> getSessions() async => [];

  @override
  Future<List<Map<String, dynamic>>> getSessionMessages(int sessionId) async => [];
}

void main() {
  group('TEST-UNIT-CHATBOT: ChatbotController', () {
    late MockChatbotRepository mockRepo;
    late ChatbotController controller;

    setUp(() {
      mockRepo = MockChatbotRepository();
      controller = ChatbotController(mockRepo);
    });

    test('Initial state contains greeting message and no active session', () {
      expect(controller.state.messages.length, 1);
      expect(controller.state.messages.first.sender, 'bot');
      expect(controller.state.sessionId, isNull);
      expect(controller.state.isLoading, isFalse);
    });

    test('Successful message updates session_id, adds bot answer with citation', () async {
      await controller.sendMessage('Bagaimana syarat KTP hilang?');

      expect(mockRepo.lastQuery, 'Bagaimana syarat KTP hilang?');
      expect(mockRepo.lastSessionId, isNull);
      expect(controller.state.sessionId, 10);
      expect(controller.state.messages.length, 3); // greeting + user + bot

      final userMsg = controller.state.messages[1];
      expect(userMsg.sender, 'warga');
      expect(userMsg.text, 'Bagaimana syarat KTP hilang?');

      final botMsg = controller.state.messages[2];
      expect(botMsg.sender, 'bot');
      expect(botMsg.citation, 'KTP-el Hilang (RTC-014)');
      expect(botMsg.similarityScore, 0.89);
      expect(botMsg.isEscalated, isFalse);
    });

    test('Follow-up message uses existing session_id', () async {
      // First turn
      await controller.sendMessage('Pertanyaan pertama');
      expect(controller.state.sessionId, 10);

      // Second turn
      mockRepo.mockResponse = {
        'session_id': 10,
        'is_escalated': false,
        'answer': 'Jawaban lanjutan.',
        'citation': 'KTP-el Hilang (RTC-014)',
        'similarity_score': 0.85,
      };
      await controller.sendMessage('Pertanyaan lanjutan');

      expect(mockRepo.lastSessionId, 10);
      expect(controller.state.sessionId, 10);
      expect(controller.state.messages.length, 5);
    });

    test('Escalated response sets isEscalated and whatsappUrl', () async {
      mockRepo.mockResponse = {
        'session_id': 12,
        'is_escalated': true,
        'answer': 'Informasi belum ditemukan, silakan hubungi Ketua RT.',
        'citation': null,
        'similarity_score': 0.35,
        'escalation_whatsapp_url': 'https://wa.me/6281234567890',
      };

      await controller.sendMessage('Pertanyaan di luar SOP RT');

      final botMsg = controller.state.messages.last;
      expect(botMsg.isEscalated, isTrue);
      expect(botMsg.whatsappUrl, 'https://wa.me/6281234567890');
      expect(botMsg.citation, isNull);
    });

    test('Network error adds friendly fallback message without crashing', () async {
      mockRepo.mockError = Exception('Koneksi timeout');

      await controller.sendMessage('Pertanyaan saat offline');

      expect(controller.state.isLoading, isFalse);
      expect(controller.state.messages.last.sender, 'bot');
      expect(controller.state.messages.last.text, contains('terjadi kendala'));
    });
  });
}
