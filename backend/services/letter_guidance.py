"""Panduan per jenis surat untuk asisten AI dan layar pengajuan.

- tujuan_saran   : instansi tujuan yang lazim -> pilihan cepat di aplikasi & acuan AI
- contoh_keperluan: contoh kalimat keperluan baku -> acuan gaya penulisan AI
- syarat         : dokumen yang perlu disiapkan (dari kolom jenissurat.persyaratan_dokumen,
                   dengan cadangan di bawah bila kolom kosong)

SOP per jenis surat (dipakai guardrail AI, lihat services/ai_guardrails.py):
- kata_kunci   : kata yang HARUS muncul di cerita warga agar jenis surat boleh dipilih AI
- tujuan_pola  : regex instansi tujuan yang sah menurut SOP (None = bebas, asal disebut warga)
- tujuan_alias : kata di cerita warga -> nama resmi instansi tujuan
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


def _sop():
    kec, kel = Config.RT_KECAMATAN.title(), Config.RT_KELURAHAN.title()
    kantor_kel, kantor_kec = _kelurahan(), _kecamatan()
    dukcapil = 'Dinas Kependudukan dan Pencatatan Sipil Kota Surabaya'
    alias_wilayah = {
        'kelurahan': kantor_kel, 'lurah': kantor_kel,
        'kecamatan': kantor_kec, 'camat': kantor_kec,
        'dispendukcapil': dukcapil, 'dukcapil': dukcapil, 'capil': dukcapil,
    }
    return {
        'SKCK': {
            'kata_kunci': ['skck', 'catatan kepolisian', 'kelakuan baik', 'surat polisi', 'dari polisi'],
            # SOP: SKCK diterbitkan kepolisian, jadi surat pengantarnya hanya ditujukan ke kepolisian
            'tujuan_pola': r'\bpol(sek|res|resta|restabes|da|ri)\b|kepolisian|polisi',
            'tujuan_alias': {'polsek': f'Polsek {kec}', 'polisi sektor': f'Polsek {kec}',
                             'polrestabes': 'Polrestabes Surabaya', 'polres': 'Polrestabes Surabaya'},
        },
        'DOM': {
            'kata_kunci': ['domisili', 'tempat tinggal', 'bukti tinggal', 'tinggal di'],
            'tujuan_pola': None,
            'tujuan_alias': alias_wilayah,
        },
        'KTP': {
            'kata_kunci': ['ktp', 'kartu tanda penduduk', 'e-ktp', 'ektp', 'ktp-el'],
            # SOP: KTP-el hanya diurus di kelurahan/kecamatan/dispendukcapil
            'tujuan_pola': r'kelurahan|kecamatan|dispendukcapil|dukcapil|kependudukan',
            'tujuan_alias': alias_wilayah,
        },
        'SKU': {
            'kata_kunci': ['usaha', 'sku', 'warung', 'dagang', 'jualan', 'toko'],
            'tujuan_pola': None,
            'tujuan_alias': {**alias_wilayah, 'bank': 'Bank (pengajuan kredit usaha)'},
        },
        '_wilayah': [kec, kel, 'Surabaya'],
    }


def sop_for(kode_surat, nama_surat=None):
    """SOP satu jenis surat. Jenis baru di database (belum ada di daftar) memakai
    kata pada nama suratnya sebagai kata kunci dan tujuan bebas."""
    sop = _sop().get((kode_surat or '').upper())
    if sop:
        return sop
    kata = [w for w in re.findall(r'[a-z]{4,}', (nama_surat or '').lower())
            if w not in {'surat', 'pengantar', 'keterangan'}]
    return {'kata_kunci': kata, 'tujuan_pola': None, 'tujuan_alias': {}}


def wilayah_words():
    """Nama wilayah RT (boleh muncul di nama instansi resmi meski tidak disebut warga)."""
    return [w for nama in _sop()['_wilayah'] for w in nama.lower().split()]


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
