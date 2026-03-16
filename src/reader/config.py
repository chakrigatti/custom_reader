from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///reader.db"
    server_url: str = "http://localhost:8000"
    nitter_instance: str = "https://nitter.net"

    model_config = {"env_prefix": "READER_"}


settings = Settings()
