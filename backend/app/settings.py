import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

# Load .env file from project root
env_file = Path(__file__).parent.parent.parent / ".env"

class Settings(BaseSettings):
    DATABASE_URL: str = Field(
        default="sqlite:///./blockverify.db", 
        env="DATABASE_URL"
    )
    ISSUER_KEY_FILE: str = Field(
        default="issuer_ed25519.jwk",
        env="ISSUER_KEY_FILE"
    )
    CHAIN_RPC_URL: str = Field(
        default="https://rpc-amoy.polygon.technology",
        env="CHAIN_RPC_URL"
    )
    BULLETIN_ADDRESS: str = Field(
        default="0x61cc6944583CB81BF4fCB53322Be1bc16d68A5d7",
        env="BULLETIN_ADDRESS"
    )
    PRIVATE_KEY: str = Field(
        default="",
        env="PRIVATE_KEY"
    )
    
    model_config = {
        'env_file': str(env_file) if env_file.exists() else None,
        'env_file_encoding': 'utf-8',
        'extra': 'ignore'
    }

settings = Settings()
