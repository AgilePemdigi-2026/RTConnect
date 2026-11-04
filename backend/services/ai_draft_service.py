"""Pembuatan draf Surat Pengantar / Keterangan berbasis template (tanpa API AI).

Template disimpan di ``backend/templates/surat_pengantar.txt`` dengan penanda
``{{nama_field}}``. Penanda diganti dengan data akun warga dan data yang diisi
pemohon di form pengajuan. Template bisa diedit tanpa mengubah kode.
"""

import re
from pathlib import Path

from config import Config
from services.applicant_data import format_tanggal

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / 'templates' / 'surat_pengantar.txt'
_PLACEHOLDER = re.compile(r'\{\{\s*([a-z_]+)\s*\}\}')


def build_letter_fields(resident_data: dict, keperluan: str, applicant: dict | None = None) -> dict:
    """Kumpulkan semua nilai untuk penanda template / PDF (kunci = nama field API)."""
    applicant = applicant or {}
    nomor_rt = resident_data.get('nomor_rt') or Config.RT_NUMBER
    nomor_rw = resident_data.get('nomor_rw') or Config.RW_NUMBER
    alamat = resident_data.get('alamat') or '-'
    return {
        'rt': nomor_rt,
        'rw': nomor_rw,
        'perumahan': Config.RT_PERUMAHAN,
        'kelurahan': Config.RT_KELURAHAN,
        'kecamatan': Config.RT_KECAMATAN,
        'kabupaten': Config.RT_KABUPATEN,
        'nama': resident_data.get('nama_lengkap') or '-',
        'nik': resident_data.get('nik') or '-',
        'alamat': f'{alamat}, RT {nomor_rt} / RW {nomor_rw}',
        'pekerjaan': applicant.get('pekerjaan') or '-',
        'jenis_kelamin': applicant.get('jenis_kelamin') or '-',
        'tempat_lahir': applicant.get('tempat_lahir') or '-',
        'tanggal_lahir': format_tanggal(applicant.get('tanggal_lahir')),
        'agama': applicant.get('agama') or '-',
        'status_kawin': applicant.get('status_kawin') or '-',
        'kewarganegaraan': applicant.get('kewarganegaraan') or 'WNI',
        'nomor_kk': applicant.get('nomor_kk') or '-',
        'tujuan': applicant.get('tujuan') or '-',
        'keperluan': keperluan or '-',
        'keterangan_lain': applicant.get('keterangan_lain') or '-',
    }


def render_template(fields: dict) -> str:
    template = TEMPLATE_PATH.read_text(encoding='utf-8')
    return _PLACEHOLDER.sub(lambda m: str(fields.get(m.group(1), '-')), template).strip()


def generate_letter_draft(resident_data: dict, letter_type: dict, keperluan: str,
                          applicant: dict | None = None) -> str:
    """Draf surat dari template + data pemohon. ``letter_type`` dipertahankan untuk kompatibilitas."""
    return render_template(build_letter_fields(resident_data, keperluan, applicant))
