from pydantic import BaseModel, Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict # type: ignore


class DatabaseConfig(BaseModel):
    # url: PostgresDsn = PostgresDsn(url="postgresql://postgres:postgres@db:5432/postgres")
    sqlite_file_name: str = "database.db"
    url: str = f"sqlite:///{sqlite_file_name}"


class Settings(BaseSettings):
    database: DatabaseConfig = DatabaseConfig()

settings = Settings()