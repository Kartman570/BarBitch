import sys
from pydantic import BaseModel, PostgresDsn
from pydantic_settings import BaseSettings # type: ignore


class DatabaseConfig(BaseModel):
    url: PostgresDsn = PostgresDsn(url="postgresql://postgres:postgres@db:5432/postgres")


class Settings(BaseSettings):
    database: DatabaseConfig = DatabaseConfig()
    secret_key: str  # MUST be set via SECRET_KEY env var — no default
    debug: bool = True  # set DEBUG=false in production to hide /docs and /openapi.json

    def __init__(self, **data):
        super().__init__(**data)
        _UNSAFE = {"change-me-in-production", "secret", "password", "admin", "dev"}
        if self.secret_key.lower() in _UNSAFE:
            print(
                "\n[SECURITY WARNING] SECRET_KEY is set to a known-weak value. "
                "Generate a proper key: openssl rand -hex 32\n",
                file=sys.stderr,
            )


settings = Settings()