import os
import boto3
import uuid

def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "eu-central-1"),
    )

def upload_to_s3(file_obj):
    bucket = os.getenv("S3_BUCKET_NAME")
    file_id = f"{uuid.uuid4()}.pdf"
    get_s3_client().upload_fileobj(file_obj, bucket, file_id)
    return file_id

def list_files_in_bucket():
    bucket = os.getenv("S3_BUCKET_NAME")
    response = get_s3_client().list_objects_v2(Bucket=bucket)
    return [item['Key'] for item in response.get('Contents', []) if item['Key'].endswith('.pdf')]
