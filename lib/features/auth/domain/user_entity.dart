/// Domain Entity for User
class UserEntity {
  final int userId;
  final String nik;
  final String name;
  final String email;
  final String role;
  final String? phoneNumber;
  final String? address;
  final String? signatureUrl;

  const UserEntity({
    required this.userId,
    required this.nik,
    required this.name,
    required this.email,
    required this.role,
    this.phoneNumber,
    this.address,
    this.signatureUrl,
  });

  int get id => userId;
  String get namaLengkap => name;
  String? get nomorTelepon => phoneNumber;
  String? get alamat => address;

  bool get isRT => role.toLowerCase() == 'rt';
  bool get isWarga => role.toLowerCase() == 'warga';

  factory UserEntity.fromJson(Map<String, dynamic> json) {
    return UserEntity(
      userId: json['user_id'] as int? ?? json['id'] as int? ?? 0,
      nik: json['nik']?.toString() ?? '',
      name: json['nama_lengkap']?.toString() ?? json['name']?.toString() ?? '',
      email: json['email']?.toString() ?? '',
      role: json['role']?.toString() ?? 'warga',
      phoneNumber: json['nomor_telepon']?.toString() ?? json['phoneNumber']?.toString(),
      address: json['alamat']?.toString() ?? json['address']?.toString(),
      signatureUrl: json['tanda_tangan_digital']?.toString() ?? json['signatureUrl']?.toString(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'user_id': userId,
      'nik': nik,
      'nama_lengkap': name,
      'email': email,
      'role': role,
      'nomor_telepon': phoneNumber,
      'alamat': address,
      'tanda_tangan_digital': signatureUrl,
    };
  }
}
