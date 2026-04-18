from pydantic import BaseModel, PostgresDsn
from pydantic_settings import BaseSettings # type: ignore


class DatabaseConfig(BaseModel):
    url: PostgresDsn = PostgresDsn(url="postgresql://postgres:postgres@db:5432/postgres")


class Settings(BaseSettings):
    database: DatabaseConfig = DatabaseConfig()
    secret_key: str = "change-me-in-production"

settings = Settings()