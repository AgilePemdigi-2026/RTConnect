from config import Config


def generate_letter_draft(resident_data: dict, letter_type: dict, keperluan: str) -> str:
    """
    Build a deterministic draft from resident data and a reviewed template.
    This function does not call a generative AI model.
    """
    nama = resident_data.get('nama_lengkap', '-')
    nik = resident_data.get('nik', '-')
    alamat = resident_data.get('alamat', '-')
    nomor_rt = resident_data.get('nomor_rt', '032')
    nomor_rw = resident_data.get('nomor_rw', '08')
    draft_text = (
        f"Yang bertanda tangan di bawah ini Ketua RT {nomor_rt} RW {nomor_rw} "
        f"{Config.RT_AREA}, dengan ini menerangkan dengan sebenarnya bahwa:\n\n"
        f"  Nama Lengkap  : {nama}\n"
        f"  NIK           : {nik}\n"
        f"  Alamat Tinggal: {alamat}, RT {nomor_rt} / RW {nomor_rw}\n\n"
        f"Adalah benar warga yang bertempat tinggal di lingkungan kami dan berkelakuan baik. "
        f"Surat keterangan ini dibuat secara resmi untuk keperluan: {keperluan}.\n\n"
        f"Demikian surat pengantar/keterangan ini diberikan kepada yang bersangkutan "
        f"untuk dapat dipergunakan sebagaimana mestinya dan berlaku selama 30 hari sejak tanggal diterbitkan."
    )

    return draft_text
