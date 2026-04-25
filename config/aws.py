from typing import Optional
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AWSConfig(BaseSettings):
    """AWS Config (All the env variables should start with AWS_)"""

    ACCESS_KEY_ID: Optional[SecretStr] = None
    """Access key id"""
    SECRET_ACCESS_KEY: Optional[SecretStr] = None
    """Secret access key"""
    REGION: Optional[str] = None
    """Region, e.g. ap-south-1"""
    SQS_QUEUE_NAME: str
    """SQS Queue Name"""
    SQS_QUEUE_URL: str
    """SQS Queue URL"""

    model_config = SettingsConfigDict(
        env_file=".env", cache_strings=True, extra="ignore", env_prefix="AWS_"
    )


aws_config = AWSConfig()
