import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../auth/presentation/auth_controller.dart';
import '../data/profile_repository.dart';

final profileRepositoryProvider = Provider<ProfileRepository>((ref) {
  return ProfileRepository();
});

class ProfileState {
  final bool isLoading;
  final String? errorMessage;
  final String? successMessage;

  const ProfileState({
    this.isLoading = false,
    this.errorMessage,
    this.successMessage,
  });

  ProfileState copyWith({
    bool? isLoading,
    String? errorMessage,
    String? successMessage,
  }) {
    return ProfileState(
      isLoading: isLoading ?? this.isLoading,
      errorMessage: errorMessage,
      successMessage: successMessage,
    );
  }
}

final profileControllerProvider =
    StateNotifierProvider<ProfileController, ProfileState>((ref) {
  final repo = ref.watch(profileRepositoryProvider);
  return ProfileController(repo, ref);
});

class ProfileController extends StateNotifier<ProfileState> {
  final ProfileRepository _repository;
  final Ref _ref;

  ProfileController(this._repository, this._ref) : super(const ProfileState());

  Future<bool> updateProfile({
    required String namaLengkap,
    required String nomorTelepon,
    required String alamat,
    required String email,
  }) async {
    state = state.copyWith(isLoading: true, errorMessage: null, successMessage: null);
    try {
      final updatedUser = await _repository.updateProfile(
        namaLengkap: namaLengkap,
        nomorTelepon: nomorTelepon,
        alamat: alamat,
        email: email,
      );
      _ref.read(authControllerProvider.notifier).updateCurrentUser(updatedUser);
      state = state.copyWith(
        isLoading: false,
        successMessage: 'Profil berhasil diperbarui',
      );
      return true;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: e.toString().replaceAll('Exception: ', ''),
      );
      return false;
    }
  }

  Future<bool> updateSignature({
    String? signatureKey,
    String? filePath,
    List<int>? fileBytes,
    String? fileName,
  }) async {
    state = state.copyWith(isLoading: true, errorMessage: null, successMessage: null);
    try {
      final newSig = await _repository.updateSignature(
        signatureKey: signatureKey,
        filePath: filePath,
        fileBytes: fileBytes,
        fileName: fileName,
      );
      final currentUser = _ref.read(authControllerProvider).user;
      if (currentUser != null) {
        final updatedUser = currentUser.copyWith(signatureUrl: newSig);
        _ref.read(authControllerProvider.notifier).updateCurrentUser(updatedUser);
      }
      state = state.copyWith(
        isLoading: false,
        successMessage: 'Tanda tangan digital berhasil diperbarui',
      );
      return true;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: e.toString().replaceAll('Exception: ', ''),
      );
      return false;
    }
  }

  Future<void> refreshProfile() async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final user = await _repository.getProfile();
      _ref.read(authControllerProvider.notifier).updateCurrentUser(user);
      state = state.copyWith(isLoading: false);
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: e.toString().replaceAll('Exception: ', ''),
      );
    }
  }
}
