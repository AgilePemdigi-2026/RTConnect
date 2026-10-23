"""Private local or S3-compatible storage for uploads and generated documents."""

import io
import os
import uuid
from pathlib import Path, PurePosixPath

from PIL import Image, UnidentifiedImageError

from config import Config


_ALLOWED_CATEGORIES = {'signatures', 'attachments', 'generated_letters'}
_ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}
_ALLOWED_ATTACHMENT_EXTENSIONS = _ALLOWED_IMAGE_EXTENSIONS | {'pdf'}


def _s3_client():
    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError('boto3 is required when STORAGE_BACKEND is set to s3.') from exc
    options = {
        'region_name': Config.S3_REGION,
        'endpoint_url': Config.S3_ENDPOINT_URL,
    }
    if Config.S3_ACCESS_KEY_ID:
        options['aws_access_key_id'] = Config.S3_ACCESS_KEY_ID
    if Config.S3_SECRET_ACCESS_KEY:
        options['aws_secret_access_key'] = Config.S3_SECRET_ACCESS_KEY
    return boto3.client('s3', **options)


def _validate_key(key):
    path = PurePosixPath(key)
    if path.is_absolute() or not path.parts or any(part in {'', '.', '..'} for part in path.parts):
        raise ValueError('Invalid storage key.')
    if path.parts[0] not in _ALLOWED_CATEGORIES:
        raise ValueError('Unsupported storage category.')
    return path


def _local_path(key):
    relative = _validate_key(key)
    root = os.path.abspath(Config.UPLOAD_FOLDER)
    path = os.path.abspath(os.path.join(root, *relative.parts))
    if os.path.commonpath([root, path]) != root:
        raise ValueError('Invalid storage key.')
    return path


def _write_local(key, data):
    path = _local_path(key)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temporary_path = f'{path}.{uuid.uuid4().hex}.tmp'
    try:
        with open(temporary_path, 'wb') as output:
            output.write(data)
        os.replace(temporary_path, path)
    finally:
        if os.path.exists(temporary_path):
            os.remove(temporary_path)


def store_bytes(key, data, content_type):
    _validate_key(key)
    if Config.STORAGE_BACKEND == 's3':
        _s3_client().put_object(
            Bucket=Config.S3_BUCKET,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
    else:
        _write_local(key, data)
    return key


def read_bytes(key):
    _validate_key(key)
    if Config.STORAGE_BACKEND == 's3':
        try:
            response = _s3_client().get_object(Bucket=Config.S3_BUCKET, Key=key)
        except Exception as error:
            error_code = getattr(error, 'response', {}).get('Error', {}).get('Code')
            if error_code in {'NoSuchKey', '404', 'NotFound'}:
                raise FileNotFoundError(key) from error
            raise
        return response['Body'].read()

    with open(_local_path(key), 'rb') as source:
        return source.read()


def store_upload(upload, category):
    if category not in {'signatures', 'attachments'}:
        raise ValueError('Unsupported upload category.')
    if not upload or not upload.filename:
        raise ValueError('Choose a file to upload.')

    extension = Path(upload.filename).suffix.lower().lstrip('.')
    allowed_extensions = (
        _ALLOWED_IMAGE_EXTENSIONS if category == 'signatures'
        else _ALLOWED_ATTACHMENT_EXTENSIONS
    )
    if extension not in allowed_extensions:
        raise ValueError('Unsupported file type. Use PNG, JPG, JPEG, or PDF for attachments.')

    data = upload.stream.read(Config.MAX_UPLOAD_BYTES + 1)
    if not data:
        raise ValueError('The uploaded file is empty.')
    if len(data) > Config.MAX_UPLOAD_BYTES:
        raise ValueError('Each uploaded file must be 8 MB or smaller.')

    if extension == 'pdf':
        if not data.startswith(b'%PDF-'):
            raise ValueError('The file content does not match a PDF.')
        content_type = 'application/pdf'
    else:
        try:
            with Image.open(io.BytesIO(data)) as image:
                image.verify()
                image_format = image.format
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
            raise ValueError('The uploaded image is invalid.') from error
        expected_format = {'png': 'PNG', 'jpg': 'JPEG', 'jpeg': 'JPEG'}[extension]
        if image_format != expected_format:
            raise ValueError('The file extension does not match the image content.')
        content_type = f'image/{"jpeg" if image_format == "JPEG" else "png"}'

    key = f'{category}/{uuid.uuid4().hex}.{extension}'
    return store_bytes(key, data, content_type)
