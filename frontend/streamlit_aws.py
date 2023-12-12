import streamlit as st
import boto3
from io import BytesIO

# Initialize the boto3 S3 client with hardcoded credentials
# s3_client = boto3.client(
#     service_name="s3",
#     region_name="us-east-1",
#     aws_access_key_id="AKIA37JWDCIQ6ZID6PVM",
#     aws_secret_access_key="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",
# )


def upload_file_to_s3(s3_client, bucket_name, file, folder_name, file_name):
    """
    Upload a file to an S3 bucket inside a specific folder

    :param bucket_name: Bucket to upload to
    :param file: File to upload
    :param folder_name: Folder in the bucket where the file will be uploaded
    :param file_name: The name of the file to be uploaded
    """
    object_name = f"{folder_name}/{file_name}"
    try:
        s3_client.upload_fileobj(file, bucket_name, object_name)
        return True
    except Exception as e:
        print(e)
        return False
