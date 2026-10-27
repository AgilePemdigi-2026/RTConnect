import 'package:flutter_test/flutter_test.dart';
import 'package:rtconnect/features/auth/domain/auth_validators.dart';

void main() {
  group('TEST-UNIT-001: AuthValidators.validateNIK', () {
    test('rejects empty or null string', () {
      expect(AuthValidators.validateNik(null), 'NIK wajib diisi');
      expect(AuthValidators.validateNik(''), 'NIK wajib diisi');
      expect(AuthValidators.validateNik('   '), 'NIK wajib diisi');
    });

    test('rejects NIK with length != 16', () {
      expect(AuthValidators.validateNik('12345'), 'NIK harus terdiri dari 16 digit');
      expect(AuthValidators.validateNik('351508210499000199'), 'NIK harus terdiri dari 16 digit');
    });

    test('rejects NIK with non-digit characters', () {
      expect(AuthValidators.validateNik('351508210499000a'), 'NIK harus berupa angka');
      expect(AuthValidators.validateNik('35150821-4990001'), 'NIK harus berupa angka');
    });

    test('accepts valid 16-digit numeric NIK', () {
      expect(AuthValidators.validateNik('3515082104990001'), isNull);
      expect(AuthValidators.validateNIK('3515082104990002'), isNull);
    });
  });

  group('AuthValidators.validateEmail', () {
    test('rejects invalid email formats', () {
      expect(AuthValidators.validateEmail(null), 'Email wajib diisi');
      expect(AuthValidators.validateEmail('invalid-email'), 'Format email tidak valid');
      expect(AuthValidators.validateEmail('user@'), 'Format email tidak valid');
    });

    test('accepts valid email', () {
      expect(AuthValidators.validateEmail('dhafin@example.com'), isNull);
    });
  });

  group('AuthValidators.validatePhone', () {
    test('rejects invalid phone numbers', () {
      expect(AuthValidators.validatePhone(null), 'Nomor telepon wajib diisi');
      expect(AuthValidators.validatePhone('0812'), 'Nomor telepon minimal 10 dan maksimal 15 digit');
      expect(AuthValidators.validatePhone('081234567890123456'), 'Nomor telepon minimal 10 dan maksimal 15 digit');
      expect(AuthValidators.validatePhone('0812345abcde'), 'Nomor telepon harus berupa angka');
    });

    test('accepts valid phone numbers', () {
      expect(AuthValidators.validatePhone('081234567890'), isNull);
      expect(AuthValidators.validatePhone('0812987654321'), isNull);
    });
  });

  group('AuthValidators.validatePassword', () {
    test('rejects short passwords', () {
      expect(AuthValidators.validatePassword(null), 'Password wajib diisi');
      expect(AuthValidators.validatePassword('12345'), 'Password minimal 6 karakter');
    });

    test('accepts valid password', () {
      expect(AuthValidators.validatePassword('rahasia123'), isNull);
    });
  });
}
