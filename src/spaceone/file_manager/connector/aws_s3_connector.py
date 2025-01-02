import logging
import boto3
from io import BytesIO
import botocore

from spaceone.core.error import *
from spaceone.file_manager.connector.file_base_connector import FileBaseConnector

__all__ = ["AWSS3Connector"]
_LOGGER = logging.getLogger(__name__)


class AWSS3Connector(FileBaseConnector):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.client = None
        self.bucket_name = None
        self._create_session()
        self._set_bucket()

    def _create_session(self):
        aws_access_key_id = self.config.get("aws_access_key_id")
        aws_secret_access_key = self.config.get("aws_secret_access_key")
        region_name = self.config.get("region_name")

        if region_name is None:
            raise ERROR_CONNECTOR_CONFIGURATION(backend="AWSS3Connector")

        if aws_access_key_id and aws_secret_access_key:
            self.client = boto3.client(
                "s3",
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region_name,
            )
        else:
            self.client = boto3.client("s3", region_name=region_name)

    def _set_bucket(self):
        bucket_name = self.config.get("bucket_name")

        if bucket_name is None:
            raise ERROR_CONNECTOR_CONFIGURATION(backend="AWSS3Connector")

        self.bucket_name = bucket_name

    def get_upload_url(self, file_id, file_name):
        object_name = self._generate_object_name(file_id, file_name)
        response = self.client.generate_presigned_post(self.bucket_name, object_name)
        return response["url"], response["fields"]

    def get_download_url(self, file_id, file_name):
        object_name = self._generate_object_name(file_id, file_name)
        response = self.client.generate_presigned_url(
            "get_object", Params={"Bucket": self.bucket_name, "Key": object_name}, ExpiresIn=86400
        )

        return response

    def check_file(self, remote_file_path):
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=remote_file_path)
            return True
        except Exception as e:
            _LOGGER.debug(f"[check_file] get_object error: {e}")
            return False

    def delete_file(self, remote_file_path):
        self.client.delete_object(Bucket=self.bucket_name, Key=remote_file_path)

    @staticmethod
    def _generate_object_name(file_id, file_name):
        return f"{file_id}/{file_name}"


    def upload_file(self, remote_file_path:str, data: bytes) -> None:
        file_obj =  BytesIO(data)
        if self.client is None:
            raise ERROR_CONNECTOR_CONFIGURATION(backend="AWSS3Connector")
        self.client.upload_fileobj(file_obj, self.bucket_name, remote_file_path)
    
    def download_file(self, remote_file_path:str) :
        
        if self.client is None:
            raise ERROR_CONNECTOR_CONFIGURATION(backend="AWSS3Connector")
        
        # S3 객체 가져오기
        obj = self.client.get_object(Bucket=self.bucket_name, Key=remote_file_path)
        
        # 파일 크기 출력
        # print(f"File size: {obj['ContentLength']} bytes")
        # S3 스트리밍 바디 얻기
        return obj["Body"]
