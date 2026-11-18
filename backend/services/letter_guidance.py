"""Panduan per jenis surat untuk asisten AI dan layar pengajuan.

- tujuan_saran   : instansi tujuan yang lazim -> pilihan cepat di aplikasi & acuan AI
- contoh_keperluan: contoh kalimat keperluan baku -> acuan gaya penulisan AI
- syarat         : dokumen yang perlu disiapkan (dari kolom jenissurat.persyaratan_dokumen,
                   dengan cadangan di bawah bila kolom kosong)
"""
import re

from config import Config


def _kelurahan():
    return f'Kantor Kelurahan {Config.RT_KELURAHAN.title()}'


def _kecamatan():
    return f'Kantor Kecamatan {Config.RT_KECAMATAN.title()}'


def _guidance():
    return {
        'SKCK': {
            'tujuan_saran': [f'Polsek {Config.RT_KECAMATAN.title()}', 'Polrestabes Surabaya'],
            'contoh_keperluan': [
                'Persyaratan melamar pekerjaan di PT Maju Jaya',
                'Persyaratan pendaftaran calon mahasiswa',
            ],
            'syarat': ['KTP asli', 'Kartu Keluarga'],
        },
        'DOM': {
            'tujuan_saran': [_kelurahan(), _kecamatan()],
            'contoh_keperluan': [
                'Persyaratan pembukaan rekening bank',
                'Persyaratan administrasi tempat kerja',
            ],
            'syarat': ['KTP', 'Bukti tempat tinggal (PBB/sewa)'],
        },
        'KTP': {
            'tujuan_saran': [_kelurahan(), 'Dinas Kependudukan dan Pencatatan Sipil Kota Surabaya'],
            'contoh_keperluan': [
                'Pengurusan KTP-el baru',
                'Perpanjangan/penggantian KTP-el yang rusak',
            ],
            'syarat': ['Fotokopi Kartu Keluarga', 'KTP lama (bila ada)'],
        },
        'SKU': {
            'tujuan_saran': [_kelurahan(), 'Bank (pengajuan kredit usaha)'],
            'contoh_keperluan': [
                'Persyaratan pengajuan kredit usaha mikro di bank',
                'Persyaratan pendaftaran izin usaha mikro',
            ],
            'syarat': ['Foto tempat usaha', 'KTP pemilik usaha'],
        },
    }


def _split_syarat(text):
    if not text:
        return []
    parts = re.split(r',|;|\bdan\b', str(text))
    return [p.strip(' .') for p in parts if p.strip(' .')]


def guidance_for(kode_surat, persyaratan_dokumen=None):
    """Panduan untuk satu jenis surat. Selalu mengembalikan dict lengkap."""
    base = _guidance().get((kode_surat or '').upper(), {})
    syarat = _split_syarat(persyaratan_dokumen) or list(base.get('syarat', []))
    return {
        'tujuan_saran': list(base.get('tujuan_saran', [_kelurahan()])),
        'contoh_keperluan': list(base.get('contoh_keperluan', [])),
        'syarat': syarat,
    }


def prompt_lines(letter_types):
    """Baris panduan per jenis surat untuk disisipkan ke prompt AI."""
    lines = []
    for item in letter_types:
        g = guidance_for(item.get('kode_surat'), item.get('persyaratan_dokumen'))
        lines.append(
            f"- {item['kode_surat']}: tujuan lazim {', '.join(g['tujuan_saran'])}; "
            f"contoh keperluan: {' | '.join(g['contoh_keperluan']) or '-'}"
        )
    return '\n'.join(lines)
