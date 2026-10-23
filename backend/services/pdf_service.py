import os
import datetime
import io
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
from config import Config
from services.file_storage import read_bytes


def _user_paragraph(value, style):
    return Paragraph(escape(str(value or '-')).replace('\n', '<br/>'), style)

def generate_official_letter_pdf(
    application: dict,
    resident: dict,
    letter_type: dict,
    official_letter_number: str,
    rt_user: dict,
    output_filename: str = None
) -> str:
    """
    Menghasilkan file PDF surat dengan kop komunitas, data pemohon,
    isi draf pengantar, dan tempelan gambar tanda tangan digital Ketua RT (UC-09).
    """
    os.makedirs(Config.LETTERS_FOLDER, exist_ok=True)

    if not output_filename:
        safe_num = official_letter_number.replace('/', '_').replace('\\', '_')
        output_filename = f"Surat_{safe_num}.pdf"

    pdf_path = os.path.join(Config.LETTERS_FOLDER, output_filename)

    # Inisialisasi dokumen A4 dengan margin standar 2 cm
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Kustomisasi styles
    header_title_style = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        alignment=1, # Center
        textColor=colors.HexColor('#0F172A')
    )
    header_subtitle_style = ParagraphStyle(
        'HeaderSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        alignment=1,
        textColor=colors.HexColor('#334155')
    )
    doc_title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        alignment=1,
        spaceAfter=3,
        textColor=colors.HexColor('#0F172A')
    )
    doc_no_style = ParagraphStyle(
        'DocNo',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        alignment=1,
        spaceAfter=15,
        textColor=colors.HexColor('#475569')
    )
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=15,
        alignment=4, # Justify
        spaceAfter=10,
        textColor=colors.HexColor('#1E293B')
    )
    table_label_style = ParagraphStyle(
        'TableLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155')
    )
    table_value_style = ParagraphStyle(
        'TableValue',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1E293B')
    )
    sign_style = ParagraphStyle(
        'SignStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=colors.HexColor('#1E293B')
    )
    sign_bold_style = ParagraphStyle(
        'SignBoldStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=colors.HexColor('#0F172A')
    )

    story = []

    # 1. KOP SURAT RT
    story.append(Paragraph(escape(Config.RT_AREA.upper()), header_title_style))
    story.append(Paragraph(escape(Config.RT_LOCATION_LINE_2), header_title_style))
    story.append(Paragraph(escape(Config.RT_LOCATION_LINE_3), header_subtitle_style))
    story.append(Spacer(1, 8))
    
    # Garis Pembatas Kop Surat
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0F172A'), spaceBefore=2, spaceAfter=2))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor('#0F172A'), spaceBefore=1, spaceAfter=14))

    # 2. JUDUL DAN NOMOR SURAT
    nama_surat_upper = letter_type.get('nama_surat', 'SURAT KETERANGAN').upper()
    story.append(Paragraph(f"<u>{escape(nama_surat_upper)}</u>", doc_title_style))
    story.append(Paragraph(f"Nomor: {escape(str(official_letter_number))}", doc_no_style))

    # 3. PARAGRAF PEMBUKA
    pembuka = (
        f"Yang bertanda tangan di bawah ini Ketua {Config.RT_AREA}, "
        f"{Config.RT_LOCATION_LINE_3}, dengan ini menerangkan bahwa:"
    )
    story.append(Paragraph(escape(pembuka), body_style))
    story.append(Spacer(1, 6))

    # 4. TABEL BIODATA PEMOHON
    data_pemohon = [
        [Paragraph("Nama Lengkap", table_label_style), Paragraph(":", table_label_style), _user_paragraph(resident.get('nama_lengkap'), table_value_style)],
        [Paragraph("NIK", table_label_style), Paragraph(":", table_label_style), _user_paragraph(resident.get('nik'), table_value_style)],
        [Paragraph("Nomor Telepon", table_label_style), Paragraph(":", table_label_style), _user_paragraph(resident.get('nomor_telepon'), table_value_style)],
        [Paragraph("Alamat Tinggal", table_label_style), Paragraph(":", table_label_style), _user_paragraph(f"{resident.get('alamat', '-')}, RT {resident.get('nomor_rt', '032')}/RW {resident.get('nomor_rw', '08')}", table_value_style)],
        [Paragraph("Keperluan", table_label_style), Paragraph(":", table_label_style), _user_paragraph(application.get('keperluan'), table_value_style)]
    ]

    t = Table(data_pemohon, colWidths=[120, 15, 350])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    # 5. PARAGRAF ISI / DRAF KETERANGAN
    draf_isi = application.get('draf_ai_konten') or (
        f"Orang tersebut di atas adalah benar-benar warga yang bertempat tinggal di lingkungan {Config.RT_AREA} "
        "dan berkelakuan baik dalam kehidupan bermasyarakat."
    )
    
    # Ambil paragraf penjelas jika draf mengandung baris-baris
    lines = [l.strip() for l in draf_isi.split('\n') if l.strip()]
    if lines:
        for line in lines:
            if not line.startswith("Nama Lengkap") and not line.startswith("NIK") and not line.startswith("Alamat Tinggal"):
                story.append(_user_paragraph(line, body_style))
    else:
        story.append(_user_paragraph(draf_isi, body_style))

    story.append(Spacer(1, 8))

    # 6. PARAGRAF PENUTUP
    penutup = (
        "Demikian surat keterangan/pengantar ini kami berikan dengan sebenarnya "
        "agar dapat dipergunakan sebagaimana mestinya oleh pihak yang berkepentingan. "
        "Surat ini berlaku selama 30 (tiga puluh) hari kalender sejak tanggal diterbitkan."
    )
    story.append(Paragraph(penutup, body_style))
    story.append(Spacer(1, 16))

    # 7. BLOK TANDA TANGAN KETUA RT DENGAN TEMPELAN GAMBAR TANDA TANGAN DIGITAL (UC-09)
    today_formatted = datetime.date.today().strftime('%d %B %Y')
    rt_name = rt_user.get('nama_lengkap', Config.RT_NAME)

    # Cek lokasi file tanda tangan digital RT
    signature_key = rt_user.get('tanda_tangan_url')

    # Komponen tanda tangan
    sign_flowables = [
        Paragraph(f"{escape(Config.RT_SIGNING_LOCATION)}, {today_formatted}", sign_style),
        Paragraph(f"Ketua RT {escape(Config.RT_NUMBER)} RW {escape(Config.RW_NUMBER)}", sign_bold_style),
        Spacer(1, 4)
    ]

    if signature_key:
        try:
            signature_bytes = read_bytes(signature_key)
        except FileNotFoundError:
            signature_bytes = None
    else:
        signature_bytes = None

    if signature_bytes:
        sig_img = Image(io.BytesIO(signature_bytes), width=140, height=48)
        sign_flowables.append(sig_img)
    else:
        sign_flowables.append(Spacer(1, 48))

    sign_flowables.append(Spacer(1, 4))
    sign_flowables.append(Paragraph(f"<b><u>( {escape(str(rt_name))} )</u></b>", sign_bold_style))
    sign_flowables.append(Paragraph("Pengesahan Ketua RT melalui PIN; tanda tangan berupa gambar", ParagraphStyle('SignSub', parent=sign_style, fontSize=8, textColor=colors.HexColor('#64748B'))))

    # Letakkan tanda tangan di sisi kanan dokumen
    sign_table_data = [
        ["", sign_flowables]
    ]
    sign_table = Table(sign_table_data, colWidths=[280, 200])
    sign_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,-1), 'CENTER'),
    ]))

    story.append(sign_table)

    # Build PDF
    doc.build(story)
    return pdf_path
