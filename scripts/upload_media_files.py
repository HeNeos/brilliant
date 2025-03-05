import mimetypes
import os
import time

import boto3


def is_binary(file_path):
    """Check if a file contains binary content by looking for null bytes."""
    with open(file_path, "rb") as f:
        content = f.read()
        return b"\x00" in content


def upload_to_s3(local_path, bucket, s3_base_path=""):
    """
    Upload files to S3 with the following rules:
    - Skip files larger than 500KB
    - SVG files detected as binary get 'binary/octet-stream' content type
    - Other files get appropriate MIME type
    """
    s3 = boto3.client("s3")

    for root, _, files in os.walk(local_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)

            file_size = os.path.getsize(file_path)
            if file_size > 500 * 1024:  # 500KB limit
                print(
                    f"Skipping {file_path} ({file_size/1024:.2f}KB exceeds 500KB limit)"
                )
                continue

            # Determine content type
            content_type = None
            if file_name.lower().endswith(".svg"):
                if is_binary(file_path):
                    content_type = "binary/octet-stream"
                else:
                    content_type = "image/svg+xml"
            else:
                content_type, _ = mimetypes.guess_type(file_path)
                content_type = content_type or "binary/octet-stream"

            relative_path = os.path.relpath(file_path, start=local_path)
            s3_key = os.path.join(s3_base_path, relative_path).replace("\\", "/")

            try:
                s3.upload_file(
                    Filename=file_path,
                    Bucket=bucket,
                    Key=s3_key,
                    ExtraArgs={"ContentType": content_type},
                )
                print(
                    f"Uploaded {file_path} to s3://{bucket}/{s3_key} ({content_type})"
                )
                time.sleep(1)
            except Exception as e:
                print(f"Error uploading {file_path}: {str(e)}")


if __name__ == "__main__":
    LOCAL_DIRECTORY = "/home/heneos/brilliant_problems/brioche/uploads"
    BUCKET_NAME = "brilliant-problems"
    S3_TARGET_PATH = "brioche/uploads"

    upload_to_s3(LOCAL_DIRECTORY, BUCKET_NAME, S3_TARGET_PATH)
