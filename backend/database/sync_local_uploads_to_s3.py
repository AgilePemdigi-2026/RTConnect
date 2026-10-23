"""Copy existing local uploads into the configured private S3-compatible bucket."""

import mimetypes

from config import Config
from database.db import query_all
from services.file_storage import _local_path, _s3_client, _validate_key


def main():
    if Config.STORAGE_BACKEND != 's3' or not Config.S3_BUCKET:
        raise SystemExit('Set STORAGE_BACKEND=s3 and S3_BUCKET before running this command.')

    keys = set()
    for query in (
        'SELECT tanda_tangan_url AS storage_key FROM users WHERE tanda_tangan_url IS NOT NULL',
        'SELECT berkas_lampiran_url AS storage_key FROM pengajuan_surat WHERE berkas_lampiran_url IS NOT NULL',
        'SELECT file_pdf_path AS storage_key FROM surat_final WHERE file_pdf_path IS NOT NULL',
    ):
        keys.update(row['storage_key'] for row in query_all(query) if row['storage_key'])

    s3 = _s3_client()
    copied = 0
    missing = []
    for key in sorted(keys):
        _validate_key(key)
        local_path = _local_path(key)
        try:
            with open(local_path, 'rb') as source:
                body = source.read()
        except FileNotFoundError:
            missing.append(key)
            continue
        content_type = mimetypes.guess_type(key)[0] or 'application/octet-stream'
        s3.put_object(Bucket=Config.S3_BUCKET, Key=key, Body=body, ContentType=content_type)
        copied += 1

    print(f'Copied {copied} object(s) to {Config.S3_BUCKET}.')
    if missing:
        print('These database keys had no local file and need manual recovery:')
        for key in missing:
            print(f'  - {key}')


if __name__ == '__main__':
    main()
