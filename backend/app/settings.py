from pydantic import BaseSettings, Field
class Settings(BaseSettings):
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    ISSUER_KEY_FILE: str = "issuer_ed25519.jwk"
    CHAIN_RPC_URL: str = Field(..., env="CHAIN_RPC_URL")
    BULLETIN_ADDRESS: str = Field(..., env="BULLETIN_ADDRESS")
settings = Settings()
