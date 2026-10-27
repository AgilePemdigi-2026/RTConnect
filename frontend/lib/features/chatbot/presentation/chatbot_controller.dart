import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/constants/app_constants.dart';
import '../data/chatbot_repository.dart';

class ChatMessage {
  final String sender; // 'warga' or 'bot'
  final String text;
  final String? citation;
  final double? similarityScore;
  final bool isEscalated;
  final String? whatsappUrl;
  final DateTime time;

  ChatMessage({
    required this.sender,
    required this.text,
    this.citation,
    this.similarityScore,
    this.isEscalated = false,
    this.whatsappUrl,
    DateTime? time,
  }) : time = time ?? DateTime.now();
}

class ChatState {
  final List<ChatMessage> messages;
  final bool isLoading;
  final int? sessionId;

  const ChatState({
    this.messages = const [],
    this.isLoading = false,
    this.sessionId,
  });

  ChatState copyWith({
    List<ChatMessage>? messages,
    bool? isLoading,
    int? sessionId,
  }) {
    return ChatState(
      messages: messages ?? this.messages,
      isLoading: isLoading ?? this.isLoading,
      sessionId: sessionId ?? this.sessionId,
    );
  }
}

final chatbotRepositoryProvider = Provider<ChatbotRepository>((ref) {
  return ChatbotRepository();
});

final chatbotControllerProvider = StateNotifierProvider<ChatbotController, ChatState>((ref) {
  final repo = ref.watch(chatbotRepositoryProvider);
  return ChatbotController(repo);
});

class ChatbotController extends StateNotifier<ChatState> {
  final ChatbotRepository _repo;

  ChatbotController(this._repo)
      : super(
          ChatState(
            messages: [
              ChatMessage(
                sender: 'bot',
                text: 'Halo! Saya Tanya RT untuk ${AppConstants.rtArea}. '
                    'Ada yang bisa saya bantu mengenai tata tertib, administrasi surat, atau kegiatan warga?',
              ),
            ],
          ),
        );

  Future<void> sendMessage(String text) async {
    final trimmed = text.trim();
    if (trimmed.isEmpty) return;

    // 1. Tambah pesan warga
    final userMsg = ChatMessage(sender: 'warga', text: trimmed);
    state = state.copyWith(
      messages: [...state.messages, userMsg],
      isLoading: true,
    );

    try {
      final res = await _repo.sendQuery(query: trimmed, sessionId: state.sessionId);
      final newSessionId = res['session_id'] as int?;
      final isEscalated = res['is_escalated'] == true;
      final answer = res['answer']?.toString() ?? 'Tidak ada jawaban';
      final citation = res['citation']?.toString();
      final similarity = (res['similarity_score'] as num?)?.toDouble();
      final waUrl = res['escalation_whatsapp_url']?.toString();

      final botMsg = ChatMessage(
        sender: 'bot',
        text: answer,
        citation: citation,
        similarityScore: similarity,
        isEscalated: isEscalated,
        whatsappUrl: waUrl,
      );

      state = state.copyWith(
        messages: [...state.messages, botMsg],
        isLoading: false,
        sessionId: newSessionId ?? state.sessionId,
      );
    } catch (e) {
      final botMsg = ChatMessage(
        sender: 'bot',
        text: 'Maaf, terjadi kendala saat menghubungi layanan Tanya RT: $e',
      );
      state = state.copyWith(
        messages: [...state.messages, botMsg],
        isLoading: false,
      );
    }
  }
}
