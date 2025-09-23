from pydantic_settings import BaseSettings
from typing import List, Optional
import os
import secrets


class Settings(BaseSettings):
    """Application settings"""
    # 环境变量
    
    # 公钥
    JWT_PUBLIC_KEY: Optional[str] = None
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()
