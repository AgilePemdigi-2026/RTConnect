import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../data/letter_repository.dart';

final letterRepositoryProvider = Provider<LetterRepository>((ref) {
  return LetterRepository();
});

final letterTypesProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final repo = ref.watch(letterRepositoryProvider);
  return await repo.getLetterTypes();
});

final myApplicationsProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final repo = ref.watch(letterRepositoryProvider);
  return await repo.getMyApplications();
});

final incomingQueueProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final repo = ref.watch(letterRepositoryProvider);
  return await repo.getIncomingQueue();
});

final applicationDetailProvider = FutureProvider.family<Map<String, dynamic>, int>((ref, id) async {
  final repo = ref.watch(letterRepositoryProvider);
  return await repo.getApplicationDetail(id);
});

class LetterSubmitState {
  final bool isLoading;
  final String? errorMessage;
  final Map<String, dynamic>? result;

  const LetterSubmitState({
    this.isLoading = false,
    this.errorMessage,
    this.result,
  });

  LetterSubmitState copyWith({
    bool? isLoading,
    String? errorMessage,
    Map<String, dynamic>? result,
  }) {
    return LetterSubmitState(
      isLoading: isLoading ?? this.isLoading,
      errorMessage: errorMessage,
      result: result ?? this.result,
    );
  }
}

final letterSubmitControllerProvider = StateNotifierProvider<LetterSubmitController, LetterSubmitState>((ref) {
  final repo = ref.watch(letterRepositoryProvider);
  return LetterSubmitController(repo, ref);
});

class LetterSubmitController extends StateNotifier<LetterSubmitState> {
  final LetterRepository _repo;
  final Ref _ref;

  LetterSubmitController(this._repo, this._ref) : super(const LetterSubmitState());

  Future<bool> submitApplication({
    required int jenisSuratId,
    required String keperluan,
    required String metodeTandaTangan,
    String? lampiranPath,
  }) async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final res = await _repo.applyLetter(
        jenisSuratId: jenisSuratId,
        keperluan: keperluan,
        metodeTandaTangan: metodeTandaTangan,
        lampiranPath: lampiranPath,
      );
      state = state.copyWith(isLoading: false, result: res);
      _ref.invalidate(myApplicationsProvider);
      return true;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: e.toString().replaceAll('Exception: ', ''),
      );
      return false;
    }
  }

  Future<bool> submitDecision(int id, String action, String catatan) async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final res = await _repo.submitDecision(id, action, catatan);
      state = state.copyWith(isLoading: false, result: res);
      _ref.invalidate(incomingQueueProvider);
      _ref.invalidate(applicationDetailProvider(id));
      return true;
    } catch (e) {
      state = state.copyWith(isLoading: false, errorMessage: e.toString());
      return false;
    }
  }

  Future<bool> signDigital(int id, String pin) async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final res = await _repo.signDigital(id, pin);
      state = state.copyWith(isLoading: false, result: res);
      _ref.invalidate(incomingQueueProvider);
      _ref.invalidate(applicationDetailProvider(id));
      return true;
    } catch (e) {
      state = state.copyWith(isLoading: false, errorMessage: e.toString());
      return false;
    }
  }

  Future<bool> confirmPhysical(int id) async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      await _repo.confirmPhysical(id);
      state = state.copyWith(isLoading: false);
      _ref.invalidate(incomingQueueProvider);
      _ref.invalidate(applicationDetailProvider(id));
      return true;
    } catch (e) {
      state = state.copyWith(isLoading: false, errorMessage: e.toString());
      return false;
    }
  }
}
