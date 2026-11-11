"""Data lengkap pemohon untuk Surat Pengantar / Keterangan RT.

Data ini diisi warga di form pengajuan dan disimpan PER PENGAJUAN di tabel
`pengajuansurat`, sehingga setiap surat menyimpan kondisi pemohon saat diajukan.
"""

import datetime
import re

# Pilihan baku (mengikuti isian KTP-el) supaya data seragam.
JENIS_KELAMIN = ('Laki-laki', 'Perempuan')
AGAMA = ('Islam', 'Kristen', 'Katolik', 'Hindu', 'Buddha', 'Konghucu', 'Kepercayaan terhadap Tuhan YME')
STATUS_KAWIN = ('Belum Kawin', 'Kawin', 'Cerai Hidup', 'Cerai Mati')

# nama field API -> (kolom database, label untuk pesan error)
FIELDS = {
    'pekerjaan': ('pekerjaan', 'Pekerjaan'),
    'jenis_kelamin': ('jenis_kelamin', 'Jenis kelamin'),
    'tempat_lahir': ('tempat_lahir', 'Tempat lahir'),
    'tanggal_lahir': ('tanggal_lahir', 'Tanggal lahir'),
    'agama': ('agama', 'Agama'),
    'status_kawin': ('status_kawin', 'Status perkawinan'),
    'kewarganegaraan': ('kewarganegaraan', 'Kewarganegaraan'),
    'nomor_kk': ('nomor_kk', 'Nomor KK'),
    'tujuan': ('instansi_tujuan', 'Tujuan'),
    'keterangan_lain': ('keterangan_lain', 'Keterangan lain-lain'),
}
OPTIONAL = {'keterangan_lain'}
# Field yang berbeda tiap surat: TIDAK diisi ulang dari pengajuan sebelumnya.
PER_LETTER_FIELDS = ('tujuan', 'keterangan_lain')
MAX_LENGTH = {'pekerjaan': 100, 'tempat_lahir': 100, 'kewarganegaraan': 50,
              'tujuan': 150, 'keterangan_lain': 255}

# Kolom SELECT dengan alias nama field API (dipakai di query detail / data terakhir).
SELECT_COLUMNS = ', '.join(
    f'p.{column} AS {field}' if column != field else f'p.{column}'
    for field, (column, _) in FIELDS.items()
)

_BULAN = ('Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli',
          'Agustus', 'September', 'Oktober', 'November', 'Desember')


def format_tanggal(value) -> str:
    """date/datetime/'YYYY-MM-DD' -> '17 Agustus 1990' (bahasa Indonesia)."""
    if not value:
        return '-'
    if isinstance(value, str):
        try:
            value = datetime.date.fromisoformat(value[:10])
        except ValueError:
            return value
    return f'{value.day} {_BULAN[value.month - 1]} {value.year}'


def _clean(value):
    return value.strip() if isinstance(value, str) else ''


def parse_applicant_data(data: dict, partial: bool = False):
    """Validasi input form pemohon.

    Mengembalikan (values, error). `values` berisi {kolom_database: nilai}.
    Dengan partial=True (resubmit), field yang tidak dikirim dilewati.
    """
    values = {}
    for field, (column, label) in FIELDS.items():
        if partial and field not in data:
            continue
        value = _clean(data.get(field))

        if field == 'kewarganegaraan' and not value:
            value = 'WNI'
        if not value:
            if field in OPTIONAL:
                values[column] = None
                continue
            return None, f'{label} wajib diisi'

        if field in MAX_LENGTH and len(value) > MAX_LENGTH[field]:
            return None, f'{label} maksimal {MAX_LENGTH[field]} karakter'
        if field == 'jenis_kelamin' and value not in JENIS_KELAMIN:
            return None, f"Jenis kelamin harus salah satu dari: {', '.join(JENIS_KELAMIN)}"
        if field == 'agama' and value not in AGAMA:
            return None, f"Agama harus salah satu dari: {', '.join(AGAMA)}"
        if field == 'status_kawin' and value not in STATUS_KAWIN:
            return None, f"Status perkawinan harus salah satu dari: {', '.join(STATUS_KAWIN)}"
        if field == 'nomor_kk' and not re.fullmatch(r'\d{16}', value):
            return None, 'Nomor KK harus terdiri dari tepat 16 digit angka'
        if field == 'tanggal_lahir':
            try:
                value = datetime.date.fromisoformat(value[:10])
            except ValueError:
                return None, 'Tanggal lahir tidak valid (format YYYY-MM-DD)'
            if value >= datetime.date.today() or value.year < 1900:
                return None, 'Tanggal lahir tidak masuk akal'
        values[column] = value
    return values, None


def to_api(row: dict) -> dict:
    """Ubah tanggal_lahir (date) menjadi string ISO agar konsisten di JSON."""
    if row and isinstance(row.get('tanggal_lahir'), (datetime.date, datetime.datetime)):
        row['tanggal_lahir'] = row['tanggal_lahir'].isoformat()[:10]
    return row


def columns_to_api(values: dict) -> dict:
    """{kolom_database: nilai} -> {nama_field_api: nilai}."""
    column_to_field = {column: field for field, (column, _) in FIELDS.items()}
    return {column_to_field[c]: v for c, v in values.items() if c in column_to_field}
