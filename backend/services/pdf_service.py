"""PDF Surat Pengantar / Keterangan RT, meniru blangko surat pengantar RT.

Urutan & tata letak mengikuti blangko fisik: "RT : .. RW : ..", "KELURAHAN : ..",
judul bergaris bawah + "No.", daftar isian bergaris titik-titik, "Demikian agar
mendapat bantuan seperlunya", tanda tangan pemohon (kiri) & Ketua RT (kanan),
lalu "No. ....", "Mengetahui : Ketua RW" di tengah bawah.
"""

import datetime
import io
import os
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from config import Config
from services.ai_draft_service import build_letter_fields
from services.applicant_data import format_tanggal
from services.file_storage import read_bytes

INK = colors.HexColor('#111111')
DOTS = (1, 2.2)  # pola garis titik-titik

# (label persis seperti blangko, kunci field). Label pendek ditulis berjarak seperti aslinya.
FIELD_ROWS = (
    ('Nama Lengkap', 'nama'),
    ('A l a m a t', 'alamat'),
    ('Pekerjaan', 'pekerjaan'),
    ('Jenis Kelamin', 'jenis_kelamin'),
    ('Tempat / tgl. lahir', 'tempat_tgl_lahir'),
    ('A g a m a', 'agama'),
    ('Kawin / tidak kawin', 'status_kawin'),
    ('Kewarganegaraan', 'kewarganegaraan'),
    ('Nomor KK / KTP', 'kk_ktp'),
    ('T u j u a n', 'tujuan'),
    ('K e p e r l u a n', 'keperluan'),
    ('', None),  # baris titik-titik kedua untuk keperluan (seperti blangko)
    ('Keterangan lain-lain', 'keterangan_lain'),
)


def _p(text, style):
    return Paragraph(escape(str(text)).replace('\n', '<br/>'), style)


def _signature_image(rt_user):
    key = rt_user.get('tanda_tangan_url')
    if not key:
        return None
    try:
        return Image(io.BytesIO(read_bytes(key)), width=120, height=42)
    except (FileNotFoundError, OSError, ValueError):
        return None


def generate_official_letter_pdf_bytes(
    application: dict,
    resident: dict,
    letter_type: dict,
    official_letter_number: str,
    rt_user: dict,
) -> bytes:
    buffer = io.BytesIO()
    
    fields = build_letter_fields(resident, application.get('keperluan'), application)
    fields['tempat_tgl_lahir'] = f"{fields['tempat_lahir']}, {fields['tanggal_lahir']}"
    fields['kk_ktp'] = f"{fields['nomor_kk']} / {fields['nik']}"
    if fields['keterangan_lain'] == '-':
        fields['keterangan_lain'] = ''

    base = getSampleStyleSheet()['Normal']
    body = ParagraphStyle('Body', parent=base, fontName='Times-Roman', fontSize=12.5, leading=16, textColor=INK)
    head = ParagraphStyle('Head', parent=body, fontName='Times-Bold', fontSize=13.5, leading=19)
    title = ParagraphStyle('Title', parent=head, fontSize=17, leading=21, alignment=1)
    number = ParagraphStyle('Number', parent=head, fontSize=14, alignment=1)
    center = ParagraphStyle('Center', parent=body, alignment=1)

    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=64, rightMargin=58,
                            topMargin=50, bottomMargin=40,
                            title=f'Surat Pengantar {official_letter_number}')
    width = A4[0] - 64 - 58 - 12  # lebar isi (dikurangi padding frame)
    story = []

    # 1. RT : ...  RW : ...  /  KELURAHAN : ...
    rt, rw = fields['rt'], fields['rw']
    story.append(Paragraph(
        f'RT : {escape(rt)}' + '&nbsp;' * 22 + f'RW : {escape(rw)}', head))
    story.append(Paragraph(f'<u>KELURAHAN : {escape(Config.RT_KELURAHAN.upper())}</u>', head))
    story.append(Spacer(1, 16))

    # 2. Judul + nomor
    story.append(Paragraph('<u>SURAT PENGANTAR / KETERANGAN</u>', title))
    story.append(Paragraph(f'No. {escape(str(official_letter_number))}', number))
    story.append(Spacer(1, 12))

    # 3. Isian bergaris titik-titik
    story.append(Paragraph('&nbsp;&nbsp;&nbsp;Yang bertanda tangan di bawah ini, menerangkan :', body))
    story.append(Spacer(1, 2))
    rows = []
    for label, key in FIELD_ROWS:
        value = fields.get(key, '') if key else ''
        cell = _p(value, body) if value else Paragraph('&nbsp;', body)  # baris kosong tetap setinggi baris lain
        rows.append([_p(label, body), Paragraph(':' if label else '&nbsp;', body), cell])
    label_w, colon_w = 170, 22
    table = Table(rows, colWidths=[label_w, colon_w, width - label_w - colon_w])
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('LEFTPADDING', (0, 0), (0, -1), 46),
        ('LEFTPADDING', (1, 0), (1, -1), 0),
        ('RIGHTPADDING', (1, 0), (1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LINEBELOW', (2, 0), (2, -1), 0.7, INK, None, DOTS),
    ]))
    story.append(table)
    story.append(Spacer(1, 4))
    story.append(Paragraph('Demikian agar mendapat bantuan seperlunya', ParagraphStyle(
        'Closing', parent=body, leftIndent=46)))
    story.append(Spacer(1, 14))

    # 4. Tanda tangan pemohon (kiri) & Ketua RT (kanan)
    today = format_tanggal(datetime.date.today())
    rt_name = Config.RT_CHAIR_NAME or rt_user.get('nama_lengkap') or Config.RT_NAME
    signature = _signature_image(rt_user) or Spacer(1, 42)
    left = [Paragraph('Tanda tangan', center), Paragraph('Yang bersangkutan', center),
            Spacer(1, 50), Paragraph(f'( {escape(fields["nama"])} )', center)]
    right = [Paragraph(f'{escape(Config.RT_SIGNING_LOCATION)}, {today}', center),
             Paragraph(f'Ketua RT. {escape(rt)}', center), Spacer(1, 4), signature, Spacer(1, 4),
             Paragraph(f'( {escape(rt_name)} )', center)]
    half = width / 2
    signs = Table([[left, right]], colWidths=[half, half])
    signs.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    story.append(signs)

    # 5. No. register RW + Mengetahui Ketua RW (tengah)
    story.append(Paragraph('No. ' + '.' * 44, center))
    story.append(Spacer(1, 8))
    story.append(Paragraph('Mengetahui :', center))
    story.append(Paragraph(f'Ketua RW. {escape(rw)}', center))
    story.append(Spacer(1, 52))
    rw_name = Config.RW_CHAIR_NAME or '.' * 40
    story.append(Paragraph(f'( {escape(rw_name)} )', center))

    doc.build(story)
    return buffer.getvalue()


def generate_official_letter_pdf(
    application: dict,
    resident: dict,
    letter_type: dict,
    official_letter_number: str,
    rt_user: dict,
    output_filename: str = None
) -> str:
    """
    Menghasilkan file PDF surat dan menyimpannya di filesystem lokal.
    """
    pdf_bytes = generate_official_letter_pdf_bytes(
        application=application,
        resident=resident,
        letter_type=letter_type,
        official_letter_number=official_letter_number,
        rt_user=rt_user
    )
    os.makedirs(Config.LETTERS_FOLDER, exist_ok=True)
    if not output_filename:
        safe_num = official_letter_number.replace('/', '_').replace('\\', '_')
        output_filename = f"Surat_{safe_num}.pdf"

    pdf_path = os.path.join(Config.LETTERS_FOLDER, output_filename)
    with open(pdf_path, 'wb') as f:
        f.write(pdf_bytes)
    return pdf_path
