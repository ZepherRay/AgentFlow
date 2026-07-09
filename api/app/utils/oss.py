import oss2
from config import settings
from pathlib import Path


class OSSClient:
    def __init__(self):
        self.auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
        self.bucket = oss2.Bucket(self.auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET_NAME)

    def upload(self, local_path: str, oss_key: str = None) -> str:
        if oss_key is None:
            oss_key = Path(local_path).name
        self.bucket.put_object_from_file(oss_key, local_path)
        return f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT}/{oss_key}"

    def download(self, oss_key: str, local_path: str):
        self.bucket.get_object_to_file(oss_key, local_path)

    def delete(self, oss_key: str):
        self.bucket.delete_object(oss_key)


oss_client = OSSClient() if settings.OSS_ACCESS_KEY_ID else None